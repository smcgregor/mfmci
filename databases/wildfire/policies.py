"""
A set of policy functions used to generate trajectories.
"""


def policy_factory(parameter_dictionary):
    """
    Gives a policy function defined on the two parameters.
    :param parameter_dictionary: A dictionary containing the parameters expected by the policy.
    :return: A function mapping transition tuples to actions
    """

    erc_threshold = parameter_dictionary["erc_threshold"]
    time_until_end_of_fire_season_threshold = parameter_dictionary["time_until_end_of_fire_season_threshold"]

    def policy_severity(
            transition_tuple=None,
            erc_threshold=erc_threshold,
            time_until_end_of_fire_season_threshold=time_until_end_of_fire_season_threshold):
        assert transition_tuple is not None
        additional_state = transition_tuple.get_additional_state()
        erc = additional_state["ERC"]
        time_until_end_of_fire_season = 181 - additional_state["startIndex"]
        assert erc >= 0, "ERC was {}".format(erc)
        assert erc <= 100, "ERC was {}".format(erc)
        assert time_until_end_of_fire_season <= 180,\
            "timeUntilEndOfFireSeason was {}".format(time_until_end_of_fire_season)
        assert time_until_end_of_fire_season >= 0,\
            "timeUntilEndOfFireSeason was {}".format(time_until_end_of_fire_season)
        if erc >= 95:
            return 0
        elif erc >= erc_threshold:
            return 1
        elif time_until_end_of_fire_season < time_until_end_of_fire_season_threshold:
            return 1
        else:
            return 0
    return policy_severity
