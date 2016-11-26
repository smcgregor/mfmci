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

    params = {}
    if "high_fuel_count" in parameter_dictionary.keys():

        params = {
            "split": int(parameter_dictionary["high_fuel_count"]),
            "param_name": "high_fuel_count",
            "left": {
                "split": int(parameter_dictionary["fire_size_differential_1"]),
                "param_name": "fire_size_differential",
                "left": {
                    "split": int(parameter_dictionary["fire_suppression_cost_1"]),
                    "param_name": "fire_suppression_cost",
                    "left": {
                        "split": int(parameter_dictionary["fire_days_differential_1"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    },
                    "right": {
                        "split": int(parameter_dictionary["fire_days_differential_2"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    }
                },
                "right": {
                    "split": int(parameter_dictionary["fire_suppression_cost_2"]),
                    "param_name": "fire_suppression_cost",
                    "left": {
                        "split": int(parameter_dictionary["fire_days_differential_3"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    },
                    "right": {
                        "split": int(parameter_dictionary["fire_days_differential_4"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    }
                }
            },
            "right": {
                "split": int(parameter_dictionary["fire_size_differential_2"]),
                "param_name": "fire_size_differential",
                "left": {
                    "split": int(parameter_dictionary["fire_suppression_cost_3"]),
                    "param_name": "fire_suppression_cost",
                    "left": {
                        "split": int(parameter_dictionary["fire_days_differential_5"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    },
                    "right": {
                        "split": int(parameter_dictionary["fire_days_differential_6"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    }
                },
                "right": {
                    "split": int(parameter_dictionary["fire_suppression_cost_4"]),
                    "param_name": "fire_suppression_cost",
                    "left": {
                        "split": int(parameter_dictionary["fire_days_differential_7"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    },
                    "right": {
                        "split": int(parameter_dictionary["fire_days_differential_8"]),
                        "param_name": "fire_days_differential",
                        "left": 0,
                        "right": 1
                    }
                }
            }
        }

        #params["split"] = int(parameter_dictionary["high_fuel_count"])

        #params["fire_days_differential_1"] = int(parameter_dictionary["fire_days_differential_1"])
        #params["fire_days_differential_2"] = int(parameter_dictionary["fire_days_differential_2"])
        #params["fire_days_differential_3"] = int(parameter_dictionary["fire_days_differential_3"])
        #params["fire_days_differential_4"] = int(parameter_dictionary["fire_days_differential_4"])
        #params["fire_days_differential_5"] = int(parameter_dictionary["fire_days_differential_5"])
        #params["fire_days_differential_6"] = int(parameter_dictionary["fire_days_differential_6"])
        #params["fire_days_differential_7"] = int(parameter_dictionary["fire_days_differential_7"])
        #params["fire_days_differential_8"] = int(parameter_dictionary["fire_days_differential_8"])

        #params["fire_suppression_cost_1"] = int(parameter_dictionary["fire_suppression_cost_1"])
        #params["fire_suppression_cost_2"] = int(parameter_dictionary["fire_suppression_cost_2"])
        #params["fire_suppression_cost_3"] = int(parameter_dictionary["fire_suppression_cost_3"])
        #params["fire_suppression_cost_4"] = int(parameter_dictionary["fire_suppression_cost_4"])

        #params["fire_size_differential_1"] = int(parameter_dictionary["fire_size_differential_1"])
        #params["fire_size_differential_2"] = int(parameter_dictionary["fire_size_differential_2"])

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
