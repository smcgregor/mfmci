"""
A set of policy functions used to generate trajectories.
"""


def policy_factory(parameter_dictionary):
    """
    Gives a policy function defined on the two parameters.
    :param parameter_dictionary: A dictionary containing the parameters expected by the policy.
    :return: A function mapping transition tuples to actions
    """
    erc_threshold = int(parameter_dictionary["ERC Threshold"])
    time_until_end_of_fire_season_threshold = int(parameter_dictionary["Days Until End of Season Threshold"])

    counts ={}

    def split_value(name):
        if name == "fire_ending":
            return 0
        else:
            return int(parameter_dictionary[name+"_"+str(counts[name])])

    def construct_tree(name_list):
        counts[name_list[0]] += 1
        name = name_list[0]
        if len(name_list) > 1:
            return {
                "split": split_value(name),
                "param_name": name,
                "left": construct_tree(name_list[1:]),
                "right": construct_tree(name_list[1:])
            }
        else:
            if counts[name_list[0]] % 2 == 0:
                return 1
            else:
                return 0

    if False:
        tree_policy_layers = ["high_fuel_count", "fire_size_differential", "fire_suppression_cost", "fire_days_differential"]
    elif "day_8" in parameter_dictionary.keys():
        tree_policy_layers = ["fire_ending", "high_fuel_count", "erc", "day"]
    for name in tree_policy_layers:
        counts[name] = 0
    params = construct_tree(tree_policy_layers)

    def on_policy(transition_tuple=None):
        assert transition_tuple is not None
        for action in transition_tuple.results.keys():
            if transition_tuple.results[action]["additional variables"]["on policy"] == 1.0:
                return int(action)
        assert False

    def policy_tree(transition_tuple=None, params=params):
        """

        :param transition_tuple:
        :param params: {split: #, param_name: NAME, left: {params}, right: {params}}
        :return:
        """
        assert transition_tuple is not None
        assert len(params.keys()) > 0

        def tree(values, params):
            if type(params) == int:
                return params
            val = values[params["param_name"]]
            if val <= params["split"]:
                direction = "left"
            else:
                direction = "right"
            return tree(values, params[direction])

        additional_state = transition_tuple.get_additional_state()
        result_letburn = transition_tuple.get_action_result(0)["additional variables"]
        result_suppress = transition_tuple.get_action_result(1)["additional variables"]
        vals = {}
        vals["high_fuel_count"] = int(additional_state["highFuel start"])
        vals["fire_size_differential"] = abs(int(result_letburn["SurfaceFirePixels"]) + int(result_letburn["CrownFirePixels"]) - int(result_suppress["SurfaceFirePixels"]) + int(result_suppress["CrownFirePixels"]))
        vals["fire_suppression_cost"] = int(result_suppress["fireSuppressionCost"])
        vals["fire_days_differential"] = int(result_letburn["endIndex"]) - int(result_suppress["endIndex"])
        vals["fire_ending"] = int(int(result_letburn["endIndex"]) - int(result_letburn["startIndex"]) < 8)
        vals["erc"] = int(additional_state["ERC"])
        vals["day"] = 180 - int(additional_state["startIndex"])
        assert(vals["fire_days_differential"] >= 0)
        return tree(vals, params)

    def policy_location(transition_tuple=None):
        assert transition_tuple is not None
        additional_state = transition_tuple.get_additional_state()
        location = int(additional_state["ignitionLocation"]) % 940
        assert location >= 0, "Location was {}".format(location)
        if int(additional_state["IgnitionCount"] > 1):
            return 1
        if location < 470:
            return 1
        else:
            return 0

    def policy_severity(
            transition_tuple=None,
            erc_threshold=erc_threshold,
            time_until_end_of_fire_season_threshold=time_until_end_of_fire_season_threshold):
        assert transition_tuple is not None
        additional_state = transition_tuple.get_additional_state()
        erc = int(additional_state["ERC"])
        time_until_end_of_fire_season = 181 - int(additional_state["startIndex"])
        assert type(erc) == int
        assert type(time_until_end_of_fire_season) == int
        assert erc >= 0, "ERC was {}".format(erc)
        assert erc <= 100, "ERC was {}".format(erc)
        assert time_until_end_of_fire_season <= 180,\
            "timeUntilEndOfFireSeason was {}".format(time_until_end_of_fire_season)
        assert time_until_end_of_fire_season >= 0,\
            "timeUntilEndOfFireSeason was {}".format(time_until_end_of_fire_season)
        if erc > 95:
            return 0
        elif erc_threshold > erc:
            return 0
        elif time_until_end_of_fire_season_threshold < time_until_end_of_fire_season:
            return 0
        else:
            return 1

    def policy_fuels(transition_tuple=None):
        additional_state = transition_tuple.get_additional_state()
        if float(additional_state["percentHighFuel start"]) > 0.30:
            return 1
        else:
            return 0

    if int(parameter_dictionary["Use Location Policy"]) == 1:
        return policy_location
    elif int(parameter_dictionary["Use Landscape Policy"]) == 1:
        return policy_fuels
    elif int(parameter_dictionary["Use Tree Policy"]) == 1:
        return policy_tree
    else:
        return policy_severity
