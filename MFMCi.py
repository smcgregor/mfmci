"""Construct a surrogate model from elementary state transitions
of a problem domain.


**REFERENCE:**
Based on `Batch Mode Reinforcement Learning based on the
Synthesis of Artificial Trajectories <https://goo.gl/1yveeS>`_
"""

from sklearn.neighbors import BallTree
import numpy as np
import os.path
import pickle
import csv
import math
import bz2
from MFMCiPackage.TransitionTuple import TransitionTuple

__copyright__ = "Copyright 2016, Sean McGregor"
__credits__ = ["Sean McGregor"]
__license__ = "MIT"
__author__ = ["Sean McGregor"]


class MFMCi():
    """
    This class produces a surrogate for arbitrary MDP domains using trajectory synthesis.
    The domain is constructed from a database of state transitions.\n
    """

    def __init__(self,
                 database_path=None,
                 normalization_database=None,
                 possible_actions=None,
                 visualization_variables=None,
                 pre_transition_variables=None,
                 post_transition_variables=None,
                 process_row=None,
                 non_stationary=False):
        """
        :param database_path: The name of the CSV file containing the database to synthesize trajectories from.
        :param normalization_database: The database to use when computing and normalizing the variances.
        :param possible_actions: The integer identifiers of the actions that are available.
        :param visualization_variables: The variables that should be written out for visualization.
        :param pre_transition_variables: The ordered set of variables used in the distance metric.
        :param post_transition_variables: The ordered set of variables corresponding to the result state of the
        pre_transition variables.
        :param process_row: (Optional) The function used to coerce the "additional state" variables to their proper
        type.
        :param non_stationary: Indicates whether the time step should be given arbitrarily high weight in the distance
        metric.
        :return:
        """
        if normalization_database is None:
            self.normalization_database = database_path
        else:
            self.normalization_database = normalization_database

        self.database_path = database_path
        self.database_opener = open
        if not os.path.isfile(self.database_path):
            self.database_path += ".bz2"
            self.database_opener = bz2.BZ2File

        self.PRE_TRANSITION_VARIABLES = pre_transition_variables
        self.POST_TRANSITION_VARIABLES = post_transition_variables

        self.visualization_variables = visualization_variables
        self.POSSIBLE_ACTIONS = possible_actions
        self.PROCESS_ROW = process_row
        if self.PROCESS_ROW is None:
            def no_op(_):
                pass
            self.PROCESS_ROW = no_op

        self.database = []
        self.initial_state_tuples = []

        seed = 0
        self.random_state = np.random.RandomState(seed)

        # Counter used to determine which set of trajectories are being generated.
        # This ensures states are stitched without replacement only for the
        # current set of trajectories.
        self.trajectory_set_counter = -1

        self._populate_database()
        self.distance_metric = None
        self._set_metric(non_stationary=non_stationary, process_row=self.PROCESS_ROW)

        self._build_database()

        self.lastStitchDistance = 0
        self.lastEvaluatedAction = -1

        # Variables for tracking the synthesis performance
        self.totalStitchingDistance = 0
        self.terminal = False

    def _build_database(self):
        """
        Build the ball tree associated with the current database.
        :return:
        """
        self.tree = BallTree(
            self.database,
            metric="mahalanobis",
            VI=self.distance_metric)

    def _set_metric(self, non_stationary=False, process_row=None):
        """
        Set the metric associated with the database. You must build the ball tree after setting the metric.
        :param non_stationary: A boolean indicating whether the "time step start" variable should be given
        arbitrarily large weight in the distance metric. Setting this to True will force all states
        to stitch to a state generated in the same time step. You should set this to true if the number of elapsed
        time steps is the most predictive feature of similarity.
        :param process_row: A function to process the row as it is found in the database to add derived variables.
        :return:
        """

        # Check the cache for the metric file
        variances = MFMCi.get_variances(self.normalization_database, self.database_opener, process_row)
        met = np.identity(len(self.PRE_TRANSITION_VARIABLES))
        for idx, variable in enumerate(self.PRE_TRANSITION_VARIABLES):
            if variable == "time step start" and non_stationary:
                met[idx][idx] = 99999999999999.0  #  todo: does the library still work if I set this to float(inf)?
            else:
                variance = variances[variable]
                if variance == 0:
                    variance = 1.0
                met[idx][idx] = 1.0/variance
        self.distance_metric = np.array(met)

    def _insort_merge(self, state, ns, state_summary, additional_state, is_initial, terminal):
        """Insert the values into the database, and keep it sorted assuming it is already sorted.

        If the values are already in the database, add them to the existing tuple.

        todo: refactor this
        """
        tuple_2_time_step = additional_state["time step"]
        tuple_2_trajectory_identifier = additional_state["trajectory identifier"]
        tuple_2_policy_identifier = additional_state["policy identifier"]

        lo = 0
        hi = len(self.database) - 1
        database_empty = len(self.database) < 1

        if not database_empty:
            while lo < hi:
                mid = (lo+hi)//2
                if TransitionTuple.less_than(self.database[mid],
                                             tuple_2_time_step,
                                             tuple_2_trajectory_identifier,
                                             tuple_2_policy_identifier):
                    lo = mid+1
                else:
                    hi = mid

        # Add a result to an existing Transition Set, else create and insert a new one
        if not database_empty and TransitionTuple.eq(self.database[lo],
                                                     tuple_2_time_step,
                                                     tuple_2_trajectory_identifier,
                                                     tuple_2_policy_identifier):
            self.database[lo].add_action_result(additional_state["action"],
                                                ns,
                                                state_summary,
                                                additional_state)
        else:
            t = TransitionTuple(state, terminal, is_initial, self.POSSIBLE_ACTIONS)
            t.add_action_result(additional_state["action"],
                                ns,
                                state_summary,
                                additional_state)

            # The loop above terminates
            if lo < len(self.database) and TransitionTuple.less_than(self.database[lo],
                                         tuple_2_time_step,
                                         tuple_2_trajectory_identifier,
                                         tuple_2_policy_identifier):
                self.database.insert(lo + 1, t)
            else:
                self.database.insert(lo, t)
            if t.is_initial:
                self.init_state_tuples.append(t)

    def _populate_database(self):
        """
        Load transitions into the database from the selected domain's database.
        """

        def parse_value(r):
            """
            Coerce a value to a float or return the value unchanged.
            """
            try:
                ret = float(r)
                return ret
            except ValueError:
                return r

        self.database = []
        self.column_names = []
        self.init_state_tuples = []
        with self.database_opener(self.database_path, 'rb') as csv_file:
            transitions = csv.reader(csv_file, delimiter=',')
            row = transitions.next()
            for headerValue in row:
                if headerValue:
                    self.column_names.append(headerValue.strip())
            for row in transitions:
                parsed_row = map(parse_value, row)
                state = []
                ns = []
                visualization_summary = {}
                additional_state = {}
                for idx, header_value in enumerate(self.column_names):
                    additional_state[header_value] = parsed_row[idx]
                self.PROCESS_ROW(additional_state)
                for stitchingVariableIdx, variable in enumerate(self.PRE_TRANSITION_VARIABLES):
                    state.append(additional_state[variable])
                    ns_name = self.POST_TRANSITION_VARIABLES[stitchingVariableIdx]
                    ns.append(additional_state[ns_name])
                for variable in self.visualization_variables:
                    visualization_summary[variable] = additional_state[variable]

                is_terminal = False  # no states are terminal
                is_initial = (additional_state["time step"] == 0)
                assert len(state) == len(ns)
                self._insort_merge(state, ns, visualization_summary, additional_state, is_initial, is_terminal)

    def _get_closest_transition_set(self, pre_transition_variables, k=1):
        """
        returns the closest transition set from the ball tree.
        :param pre_transition_variables: The current state of the world that we want the closest transition for.
        :return: ``(TransitionTuple, distance)`` The selected transition from the database and the
          distance to that transition.
        """
        q = np.array(pre_transition_variables)
        q = q.reshape(1, -1)
        k = min(k, len(self.database))
        (distances_array, indices_array) = self.tree.query(q, k=k, return_distance=True, sort_results=True)
        indices = indices_array[0]
        for index, i in enumerate(indices):
            if self.database[i].last_accessed_iteration != self.trajectory_set_counter:
                return self.database[i], distances_array[0][index]
        if k < 10000 and k < len(self.database):
            return self._get_closest_transition_set(pre_transition_variables, k=k*10)
        raise Exception("There were no valid points within " \
                        "{} points in a database of {} points. This failure occured when " \
                        "attempting to generate trajectory set {}".format(k,
                                                                          len(self.database),
                                                                          self.trajectory_set_counter))

    def get_trajectories(self, count=10, horizon=10, policy=None):
        """
        Helper function for generating trajectories.
        :param count: The number of trajectories to generate.
        :param horizon: The maximum length of trajectories.
        :param policy: The function used to select an action.
        :return:
        """
        assert policy is not None
        self.trajectory_set_counter += 1
        self.totalStitchingDistance = 0

        trajectories = []
        for trajectory_number in range(count):
            trajectory = []
            self.s0()  # reset the state
            terminate = False
            while not terminate and len(trajectory) < horizon:
                terminate = self.is_terminal()
                ns, terminal = self.step(policy)

                self.totalStitchingDistance += self.lastStitchDistance

                state_summary = {"action": self.lastEvaluatedAction}
                assert state_summary["action"] >= 0
                for label in ns.keys():
                    state_summary[label] = ns[label]
                trajectory.append(state_summary)
            trajectories.append(trajectory)
        return trajectories

    def get_visualization_trajectories(self, count=10, horizon=10, policy=None):
        """
        Helper function for getting trajectories and formatting them for MDPvis.
        :param count: The number of trajectories to generate.
        :param horizon: The maximum length of trajectories.
        :param policy: The function used to select an action.
        :return:
        """
        assert policy is not None
        trajectories = self.get_trajectories(count=count, horizon=horizon, policy=policy)
        return trajectories

    def step(self, policy):
        """
        Find the closest transition matching the policy.
        :param policy: The policy to select an action in this step.
        :return:
        """

        # hack for biased databases
        rejected_transition_set = True
        reset_list = []
        while rejected_transition_set:
            pre = self.preStateDistanceMetricVariables
            (post_stitch_transition_set, stitch_distance) = self._get_closest_transition_set(pre)
            action = policy(post_stitch_transition_set)
            assert action >= 0
            if action in post_stitch_transition_set.results.keys():
                rejected_transition_set = False
            else:
                reset_list.append(post_stitch_transition_set)
        for transition in reset_list:
            transition.last_accessed_iteration = -1
        self.lastStitchDistance = stitch_distance
        assert stitch_distance >= 0, "Stitch distance was {}".format(stitch_distance)
        result = post_stitch_transition_set.get_action_result(action)
        self.terminal = post_stitch_transition_set.is_terminal
        self.lastEvaluatedAction = action
        post_stitch_transition_set.last_accessed_iteration = self.trajectory_set_counter
        result["state summary variables"]["stitch distance"] = stitch_distance
        self.preStateDistanceMetricVariables = result["post transition variables"]
        return result["state summary variables"], self.terminal

    def s0(self):
        """
        Get a starting state from the domain. This gets an actual starting state from the
        domain under the assumption that these states are efficiently accessible.
        If the starting state is not efficiently accessible from the true domain simulator,
        then they could be cached for repeated use under many different policies.
        :return: ``state`` for the starting state.
        """
        self.terminal = False
        self.state = {}  # There is no state until it is stitched and the complete state is recovered
        idx = int(math.floor(self.random_state.uniform() * len(self.init_state_tuples)))
        self.preStateDistanceMetricVariables = self.init_state_tuples[idx].preStateDistanceMetricVariables
        return self.state.copy(), self.terminal

    def is_terminal(self):
        """
        :return: ``True`` if the agent has reached or exceeded the goal position.
        """
        return self.terminal

    @staticmethod
    def get_variances(database_path, opener, process_row):
        """
        Find the variances of database.
        E(x^2) - E(x)^2
        :param database_path: The file name of the database we are finding the variances for.
        :param opener: The function that will read the database. This will either be `open` or bz2's open.
        :param process_row: The function used to process the row.
        :return: The variance.
        """
        variances_filename = database_path + ".variances.pkl"
        arrays = {}
        if not os.path.isfile(variances_filename):
            with opener(database_path, 'rb') as csv_file:
                transitions_reader = csv.DictReader(csv_file)
                transitions = list(transitions_reader)
                for k in transitions[0].keys():
                    for idx, transitionDictionary in enumerate(transitions):
                        transitionDictionary[k] = MFMCi.parse_value(transitionDictionary[k])
                for t in transitions:
                    process_row(t)
                for k in transitions[0]:
                    if type(transitions[0][k]) == float or type(transitions[0][k]) == int:
                        arrays[k] = []
                for k in arrays.keys():
                    for idx, transitionDictionary in enumerate(transitions):
                        arrays[k].append(transitionDictionary[k])
            variances_dict = {}
            for k in arrays.keys():
                variances_dict[k] = np.var(arrays[k])
            f = open(variances_filename, "w")
            pickle.dump(variances_dict, f)
            f.close()
        f = open(variances_filename, "rb")
        variances_dict = pickle.load(f)
        f.close()
        return variances_dict

    @staticmethod
    def parse_value(r):
        """
        Coerce a value to a float or return the value unchanged.
        :param r: The row value we are parsing.
        :return:
        """
        if type(r) is list:
            return r
        try:
            ret = float(r)
            return ret
        except ValueError:
            return r
