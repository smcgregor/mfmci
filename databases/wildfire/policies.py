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

    def on_policy(transition_tuple=None):
        assert transition_tuple is not None
        for action in transition_tuple.results.keys():
            if transition_tuple.results[action]["additional variables"]["on policy"] == 1.0:
                return int(action)
        assert False
    #return on_policy

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
    else:
        return policy_severity
