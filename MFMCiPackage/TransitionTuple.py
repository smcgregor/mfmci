class TransitionTuple(tuple):
    """
    A Simple tuple class for storing state transitions in the Ball tree.
    The object holds the tuple for the pre-transition state that will be stitched to
    in the current post-transition state. The class contains properties not in the
    tuple:
    """
    def __new__(cls, preStateDistanceMetricVariables, is_terminal, is_initial, possible_actions):
        """
        :param cls: The _new_ constructor's version of `self`
        :param preStateDistanceMetricVariables: The state we might stitch to, this is also represented as a tuple.
          These include the action indicators.
        :param is_terminal: An indicator for whether the transitioned to state is terminal.
        :param is_initial: An indicator for whether the pre-transition state is an initial state.
        :param possible_actions: What actions can be taken in the resulting state.
        :return: this extended tuple
        """
        t = tuple.__new__(cls, tuple(preStateDistanceMetricVariables))
        t.preStateDistanceMetricVariables = preStateDistanceMetricVariables
        t.is_terminal = is_terminal
        t.is_initial = is_initial
        t.possible_actions = possible_actions
        t.last_accessed_iteration = -1  # determines whether it is available for stitching
        t.results = {}
        return t

    def add_action_result(self, action, post_transition_variables, state_summary_variables, additional_variables):
        """
        Add an action result to the tuple.
        :return:
        """
        result = {
            "post transition variables": post_transition_variables,
            "state summary variables": state_summary_variables,
            "additional variables": additional_variables
        }
        assert action not in self.results
        self.results[action] = result

    def has_all_actions(self):
        """
        Helper method for checking the completeness of the database. We expect all the transition tuples to have
        transitions defined for each available actions.
        :return:
        """
        for action in self.possible_actions:
            if action not in self.results:
                return False
        return True

    def get_action_result(self, action):
        """
        Get the result state associated with the selected action.
        :return: The result state object.
        """
        return self.results[action]

    def get_additional_state(self):
        """
        Get the additional state associated with the first entry in the result dictionary. This function is
        provided to simplify evaluation of the policy.
        :return: The additional state variables associated with the first action..
        """
        return self.results[self.possible_actions[0]]["additional variables"]

    @staticmethod
    def less_than(tuple_1, tuple_2_time_step, tuple_2_trajectory_identifier, tuple_2_policy_identifier):
        """
        Compare the time step, trajectory identifier, and policy identifier to see if tuple_1 is less than tuple_2.
        :param tuple_1: The existing TransitionTuple we are comparing to.
        :param tuple_2_time_step:
        :param tuple_2_trajectory_identifier:
        :param tuple_2_policy_identifier:
        :return: boolean
        """
        tuple_1_result_set_additional_variables = tuple_1.results[tuple_1.results.keys()[0]]["additional variables"]
        if tuple_1_result_set_additional_variables["time step"] < tuple_2_time_step:
            return True
        elif tuple_1_result_set_additional_variables["time step"] > tuple_2_time_step:
            return False
        elif tuple_1_result_set_additional_variables["trajectory identifier"] < tuple_2_trajectory_identifier:
            return True
        elif tuple_1_result_set_additional_variables["trajectory identifier"] > tuple_2_trajectory_identifier:
            return False
        elif tuple_1_result_set_additional_variables["policy identifier"] < tuple_2_policy_identifier:
            return True
        elif tuple_1_result_set_additional_variables["policy identifier"] > tuple_2_policy_identifier:
            return False
        return False

    @staticmethod
    def eq(tuple_1, tuple_2_time_step, tuple_2_trajectory_identifier, tuple_2_policy_identifier):
        """
        Compare the time step, trajectory identifier, and policy identifier to see if they are all equal.
        :param tuple_1: The existing TransitionTuple we are comparing to.
        :param tuple_2_time_step:
        :param tuple_2_trajectory_identifier:
        :param tuple_2_policy_identifier:
        :return: boolean indicating whether they are equal.
        """

        tuple_1_result_set_additional_variables = tuple_1.results[tuple_1.results.keys()[0]]["additional variables"]
        if tuple_1_result_set_additional_variables["time step"] != tuple_2_time_step:
            return False
        elif tuple_1_result_set_additional_variables["trajectory identifier"] != tuple_2_trajectory_identifier:
            return False
        elif tuple_1_result_set_additional_variables["policy identifier"] != tuple_2_policy_identifier:
            return False
        return True
