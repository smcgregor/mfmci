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
import importlib
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

    def __init__(self, domain_name, database_file_name=None, include_exogenous=False):
        """
        :param domain_name: The name of the domain as given in the databases folder
        """
        self.domain_name = domain_name
        self.database_filename = "databases/" + self.domain_name + "/database.csv"
        if not (database_file_name is None):
            self.database_filename = database_file_name

        self.database_opener = open
        if not os.path.isfile(self.database_filename):
            self.database_filename += ".bz2"
            self.database_opener = bz2.BZ2File

        annotate_module = importlib.import_module("databases." + domain_name + ".annotate")
        if include_exogenous:
            self.PRE_TRANSITION_VARIABLES = annotate_module.PRE_TRANSITION_EXOGENOUS_VARIABLES
            self.POST_TRANSITION_VARIABLES = annotate_module.POST_TRANSITION_EXOGENOUS_VARIABLES
        else:
            self.PRE_TRANSITION_VARIABLES = annotate_module.PRE_TRANSITION_VARIABLES
            self.POST_TRANSITION_VARIABLES = annotate_module.POST_TRANSITION_VARIABLES

        self.exogenous_variables = set(self.PRE_TRANSITION_VARIABLES) - set(annotate_module.PRE_TRANSITION_VARIABLES)

        self.STATE_SUMMARY_VARIABLES = annotate_module.STATE_SUMMARY_VARIABLES
        self.POSSIBLE_ACTIONS = annotate_module.POSSIBLE_ACTIONS
        try:
            self.PROCESS_ROW = annotate_module.PROCESS_ROW
        except AttributeError:
            def PROCESS_ROW(x):
                pass
            self.PROCESS_ROW = PROCESS_ROW

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
        self._set_metric()

        self._build_database()

        self.lastStitchDistance = 0
        self.lastEvaluatedAction = -1

    def _build_database(self):
        """
        Build the ball tree associated with the current database.
        :return:
        """
        self.tree = BallTree(
            self.database,
            metric="mahalanobis",
            VI=self.distance_metric)

    def _set_metric(self):
        """
        Set the metric associated with the database. You must build the ball tree after setting the metric.
        :return:
        """

        # Check the cache for the metric file
        variances_filename = "databases/" + self.domain_name + "/variances.pkl"
        if not os.path.isfile(variances_filename):
            f = open(variances_filename, "w")
            variances = MFMCi.find_variances(self.database_filename, self.database_opener)
            pickle.dump(variances, f)
            f.close()
        f = open(variances_filename, "rb")
        variances = pickle.load(f)
        f.close()

        met = np.identity(len(self.PRE_TRANSITION_VARIABLES))
        for idx, variable in enumerate(self.PRE_TRANSITION_VARIABLES):
            if variable == "year start":
                met[idx][idx] = 99999999.0
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
        with self.database_opener(self.database_filename, 'rb') as csv_file:
            transitions = csv.reader(csv_file, delimiter=',')
            row = transitions.next()
            for headerValue in row:
                if headerValue:
                    self.column_names.append(headerValue.strip())
            for row in transitions:
                parsed_row = map(parse_value, row)
                state = []
                ns = []
                state_summary = {}
                additional_state = {}
                for idx, header_value in enumerate(self.column_names):
                    if header_value not in self.PRE_TRANSITION_VARIABLES \
                            and header_value not in self.POST_TRANSITION_VARIABLES:
                        additional_state[header_value] = parsed_row[idx]
                additional_state["highFuelPercent"] = parsed_row[self.column_names.index("percentHighFuel start")]
                additional_state["action"] = parsed_row[self.column_names.index("action")]
                self.PROCESS_ROW(additional_state)
                additional_state["on policy"] = (int(additional_state["on policy"]) == 1)
                for stitchingVariableIdx, variable in enumerate(self.PRE_TRANSITION_VARIABLES):
                    if variable == "year start":
                        year = parsed_row[self.column_names.index("year")]
                        state.append(year)
                        ns.append(year + 1)
                    else:
                        state_index = self.column_names.index(variable)
                        state.append(parsed_row[state_index])
                        ns_index = self.column_names.index(self.POST_TRANSITION_VARIABLES[stitchingVariableIdx])
                        ns.append(parsed_row[ns_index])
                for variable in self.STATE_SUMMARY_VARIABLES:
                    state_summary_variable_index = self.column_names.index(variable)
                    state_summary[variable] = parsed_row[state_summary_variable_index]
                state_summary["stitched policy ERC"] = additional_state["stitched policy ERC"]
                state_summary["stitched policy Days"] = additional_state["stitched policy Days"]

                is_terminal = False  # no states are terminal
                is_initial = (additional_state["time step"] == 0)
                assert len(state) == len(ns)
                self._insort_merge(state, ns, state_summary, additional_state, is_initial, is_terminal)

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
        self.totalNonZeroStitches = 0

        total_transitions = 0

        trajectories = []
        for trajectory_number in range(count):
            trajectory = []
            self.s0()  # reset the state
            terminate = False
            while not terminate and len(trajectory) < horizon:
                terminate = self.is_terminal()
                total_transitions += 1
                self.totalNonZeroStitches += 1
                ns, terminal = self.step(policy)

                self.totalStitchingDistance += self.lastStitchDistance

                state_summary = {"action": self.lastEvaluatedAction}
                assert state_summary["action"] >= 0
                for label in ns.keys():
                    state_summary[label] = ns[label]
                state_summary["image row"] = self.post_action_result["additional variables"]["image row"]
                trajectory.append(state_summary)
            trajectories.append(trajectory)
        print "Returning trajectories with {} " \
              "lossy stitched transitions for {} total transitions".format(self.totalNonZeroStitches, total_transitions)
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
        :param policy:
        :return:
        """
        action_not_found = True  # hack for biased database
        while action_not_found:
            pre = self.preStateDistanceMetricVariables
            (post_stitch_transition_set, stitch_distance) = self._get_closest_transition_set(pre)
            self.lastStitchDistance = stitch_distance
            assert stitch_distance >= 0

            action = policy(post_stitch_transition_set)
            assert action >= 0

            if action in post_stitch_transition_set.results.keys():
                action_not_found = False
            if action_not_found:
                post_stitch_transition_set.last_accessed_iteration = self.trajectory_set_counter

        post_stitch_transition_set.last_accessed_iteration = self.trajectory_set_counter
        result = post_stitch_transition_set.get_action_result(action)
        self.lastEvaluatedAction = action
        self.post_action_result = result
        self.terminal = post_stitch_transition_set.is_terminal
        self.state_summary = result["state summary variables"]

        self.state_summary["stitch distance"] = stitch_distance

        self.preStateDistanceMetricVariables = result["post transition variables"]

        lcp = result["additional variables"]["lcpFileName"].split("_")   # hack to prohibit self stitching
        self.trajectory_identifier = "{}-{}-{}".format(lcp[1], lcp[4], lcp[5])  # initial fire, ERC, DAY

        return self.state_summary, self.terminal

    def s0(self):
        """
        Get a starting state from the domain. This gets an actual starting state from the
        domain under the assumption that these states are efficiently accessible.
        If the starting state is not efficiently accessible from the true domain simulator,
        then they could be cached for repeated use under many different policies.
        :return: ``state`` for the starting state.
        """
        self.trajectory_identifier = ""  # hack to prohibit self stitching
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
    def find_variances(database_filename, opener):
        """
        Find the variances of database.
        E(x^2) - E(x)^2
        :param database_filename: The file name of the database we are finding the variances for.
        :param opener: The function that will read the database. This will either be `open` or bz2's open.
        :return: The variance.
        """

        with opener(database_filename, 'rb') as csv_file:
            transitions = csv.reader(csv_file, delimiter=',')
            row = transitions.next()
            header = []
            for headerValue in row:
                header.append(headerValue.strip())
            totals = [0.0] * len(header)
            row_count = 0.0

            for row in transitions:
                row_count += 1.0
                parsed = map(MFMCi.parse_value, row)
                for idx, val in enumerate(parsed):
                    if type(val) is float:
                        totals[idx] += val
            averages = map(lambda x: x/row_count, totals)
            totals_squared = [0.0] * len(header)
            csv_file.seek(0)
            transitions.next()  # Skip header
            for row in transitions:
                parsed = map(MFMCi.parse_value, row)
                for idx, val in enumerate(parsed):
                    if type(val) is float:
                        totals_squared[idx] += math.pow(val-averages[idx], 2.0)
        variances = map(lambda x: x/row_count, totals_squared)
        ret = {}
        for idx, column in enumerate(header):
            ret[column] = variances[idx]
        return ret

    @staticmethod
    def parse_value(r):
        """
        Coerce a value to a float or return the value unchanged.
        :param r: The row value we are parsing.
        :return:
        """
        try:
            ret = float(r)
            return ret
        except ValueError:
            return r
