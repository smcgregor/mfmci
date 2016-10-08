"""
Cross-origin MFMCi Server
===================
This is a minimal server for using MFMCi to serve your domain.

:copyright: (C) 2016 by Sean McGregor.
:license:   MIT, see LICENSE for more details.
"""
from MFMCi import MFMCi
import csv
import databases.wildfire.policies as policy_module
import numpy as np


print """
Running wildfire experiments

Please Wait (loading database)
"""

domain_name = "wildfire"
policy_factory = policy_module.policy_factory
database_sizes = [60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
database_trajectory_count = 360

visualized_variables = ["CrownFirePixels",
                        "SurfaceFirePixels",
                        "fireSuppressionCost",
                        "timberLoss_IJWF",
                        "ponderosaSC1",
                        "ponderosaSC2",
                        "ponderosaSC3",
                        "ponderosaSC4",
                        "ponderosaSC5",
                        "lodgepoleSC1",
                        "lodgepoleSC2",
                        "lodgepoleSC3",
                        "mixedConSC1",
                        "mixedConSC2",
                        "mixedConSC3",
                        "mixedConSC4",
                        "mixedConSC5",
                        "boardFeetHarvestPonderosa",
                        "boardFeetHarvestLodgepole",
                        "boardFeetHarvestMixedConifer"
                        ]

def _get_variable_height(variable_name, mc_trajectories):
    """
    Get the distance in the variable's units that the fan chart will cover.
    :param variable_name:
    :return:
    """
    maximum = float("-Inf")
    minimum = float("Inf")
    for trajectory in mc_trajectories:
        for time_step in trajectory:
            minimum = min(minimum, float(time_step[variable_name]))
            maximum = max(maximum, float(time_step[variable_name]))
    return maximum - minimum

def _get_quantile(quantile, variable_name, time_step, trajectories):
    """
    :param quantile: float [0,1] for the entry we are looking for.
    :param variable_name: the name of the variable we want the quantile for.
    :param time_step: the time step we want the quantile for.
    :param trajectories: The trajectories we are getting the quantile for.
    :return:
    """
    l = []
    for trajectory in trajectories:
        l.append(float(trajectory[time_step][variable_name]))
    l.sort()
    return l[int(quantile*len(l))]

def get_objective(mc_trajectories, mfmc_trajectories):

    # get height of each variable
    heights = {}
    for v in visualized_variables:
        heights[v] = _get_variable_height(v, mc_trajectories)

    # get each quantile and time step error for each variable, sum and return
    error = 0
    for v in visualized_variables:
        for t in range(0,99):
            actual = _get_quantile(0.5, v, t, mc_trajectories)
            synthesized = _get_quantile(0.5, v, t, mfmc_trajectories)
            if heights[v] == 0:
                assert abs(actual-synthesized) == 0, "actual: {}, {}, {}, {}, {}".format(abs(actual-synthesized), actual, synthesized, v, t)
            else:
                error += abs(actual-synthesized)/heights[v]
    return error


def bootstrap_monte_carlo_trajectories(trajectories, seed):
    """
    :param trajectories: The trajectory set we are going to bootstrap.
    :return:
    """
    random_state = np.random.RandomState(seed)
    ret = []
    while len(ret) < len(trajectories):
        idx = int(len(trajectories)*random_state.uniform())
        ret.append(trajectories[idx])
    return ret


def get_monte_carlo_trajectories(policy_name):
    """
    :param policy_name: The string identifier for the policy we want trajectories for.
    :return:
    """

    if policy_name == "location":
        database_path = "databases/wildfire/ground_truth/location_policy.csv"
    elif policy_name == "intensity":
        database_path = "databases/wildfire/ground_truth/intensity_policy.csv"
    elif policy_name == "landscape":
        database_path = "databases/wildfire/ground_truth/fuel_policy.csv"
    else:
        assert False

    trajectories = []
    trajectory = []
    with open(database_path, 'rb') as csvfile:
        transitionsReader = csv.DictReader(csvfile)
        transitions = list(transitionsReader)
        for idx, transitionDictionary in enumerate(transitions):
            if int(transitionDictionary["offPolicy"]) == 1:
                continue
            if len(trajectory) > 0:
                assert int(trajectory[-1]["year"]) == int(transitionDictionary["year"]) - 1
            trajectory.append(transitionDictionary)
            if int(transitionDictionary["year"]) == 98:
                trajectories.append(trajectory)
                trajectory = []
    return trajectories


def baseline():
    """
    Get the baseline performance of each policy by bootstrap resampling the Monte Carlo trajectories and
    evaluating the performance.
    :return:
    """
    policies = ["location", "intensity", "landscape"]
    replicates = 100
    mc_trajectories = {}
    for policy in policies:
        mc_trajectories[policy] = get_monte_carlo_trajectories(policy)
    seed = 0
    for policy in policies:
        total = 0
        for _ in range(0, replicates):
            policy_mc_trajectories = mc_trajectories[policy]
            policy_bootstrapped_mc_trajectories = bootstrap_monte_carlo_trajectories(policy_mc_trajectories, seed)
            seed += 1
            result = get_objective(policy_mc_trajectories, policy_bootstrapped_mc_trajectories)
            total += result
        print "{},{}".format(policy, total/replicates)


def experiment():
    """
    Conduct the experiments for a database size. Construct a database then compare the
    results for the policy against the Monte Carlo policy.
    :return:
    """
    policies = ["location", "intensity", "landscape"]
    mc_trajectories = {}
    for policy in policies:
        mc_trajectories[policy] = get_monte_carlo_trajectories(policy)
    for database_size in database_sizes:
        # MFMCi
        mfmci = MFMCi(domain_name,
                      database_file_name="databases/wildfire/experimental/unbiased" + str(database_size) + ".csv",
                      include_exogenous=False)
        # MFMCi with exogenous
        mfmci_exogenous = MFMCi(domain_name,
                                database_file_name="databases/wildfire/experimental/unbiased" + str(database_size) + ".csv",
                                include_exogenous=True)
        # MFMCi without bias correction
        mfmci_biased = MFMCi(domain_name,
                             database_file_name="databases/wildfire/experimental/biased" + str(database_size) + ".csv",
                             include_exogenous=False)
        for policy in policies:
            policy_mc_trajectories = mc_trajectories[policy]
            mfmci_trajectories = get_trajectories(policy, mfmci)
            mfmci_exogenous_trajectories = get_trajectories(policy, mfmci_exogenous)
            try:
                mfmci_biased_trajectories = get_trajectories(policy, mfmci_biased)
            except Exception:
                mfmci_biased_trajectories = None

            result_mfmci = get_objective(policy_mc_trajectories, mfmci_trajectories)
            result_mfmci_exogenous = get_objective(policy_mc_trajectories, mfmci_exogenous_trajectories)
            if mfmci_biased_trajectories is None:
                result_mfmci_biased = -9999999
            else:
                result_mfmci_biased = get_objective(policy_mc_trajectories, mfmci_biased_trajectories)

            unbiased_database_size = len(mfmci.database) * 2
            biased_database_size = len(mfmci_biased.database)

            print "{},{},{},{},{},{}".format(policy,
                                             unbiased_database_size,
                                             biased_database_size,
                                             result_mfmci,
                                             result_mfmci_exogenous,
                                             result_mfmci_biased)


def get_trajectories(policy_name, mfmci):
    """
        Asks the domain for the trajectories generated by the
        requested parameters.
    """
    policy_parameters = {
        "Use Location Policy": 0,
        "Use Landscape Policy": 0,
        "ERC Threshold": 65,
        "Days Until End of Season Threshold": 100
    }
    if policy_name == "location":
        policy_parameters["Use Location Policy"] = 1
    elif policy_name == "intensity":
        pass
    elif policy_name == "landscape":
        policy_parameters["Use Landscape Policy"] = 1
    else:
        assert False
    trajectories = mfmci.get_visualization_trajectories(
        count=30, horizon=99,
        policy=policy_factory(policy_parameters)
    )
    return trajectories


def _get_inclusion_order():
    """
    Get the order of inclusion as a list of random indices.
    :return:
    """
    random_state = np.random.RandomState(888939)
    eligible = range(0, database_trajectory_count)
    ordered = []
    while len(eligible) > 0:
        idx = int(len(eligible)*random_state.uniform())
        ordered.append(eligible.pop(idx))
    return ordered


def produce_smaller_databases():
    """
    Create the databases that will be used to synthesize trajectories.
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

    def write_row(row, f):
        for idx, col in enumerate(row):
            f.write(str(col))
            if idx < len(row) - 1:
                f.write(",")
        f.write("\n")

    file_references = {}
    for transition_count in database_sizes:
        file_references["biased"+str(transition_count)] = open("databases/wildfire/experimental/biased" + str(transition_count) + ".csv", "w")
        file_references["unbiased"+str(transition_count)] = open("databases/wildfire/experimental/unbiased" + str(transition_count) + ".csv", "w")

    biased_database_includes_suppress_action = False
    biased_database_includes_letburn_action = False

    column_names = []
    inclusion_order = _get_inclusion_order()
    with open("databases/wildfire/database.csv", 'rb') as csv_file:
        transitions = csv.reader(csv_file, delimiter=',')
        row = transitions.next()
        starts_of_transition_sets = []
        parsed_rows = []
        for database_size in database_sizes:
            write_row(row, file_references["biased"+str(database_size)])
            write_row(row, file_references["unbiased"+str(database_size)])

        for headerValue in row:
            if headerValue:
                h = headerValue.strip()
                column_names.append(h)
                if h == "offPolicy":
                    off_policy_index = len(column_names) - 1
                elif h == "year":
                    year_index = len(column_names) - 1
                elif h == "action":
                    action_index = len(column_names) - 1

        last = True # ensure it alternates on/off policy
        for idx, row in enumerate(transitions):
            parsed_row = map(parse_value, row)
            is_off_policy = int(parsed_row[off_policy_index]) == 1
            assert parsed_row[off_policy_index] == 1 or parsed_row[off_policy_index] == 0
            assert last != is_off_policy
            if not is_off_policy and int(parsed_row[year_index]) == 0:
                starts_of_transition_sets.append(idx)
            last = is_off_policy
            parsed_rows.append(parsed_row)

    for database_size in database_sizes:
        for transition_set_count, inclusion_idx in enumerate(inclusion_order):
            current_idx = starts_of_transition_sets[inclusion_idx]
            while current_idx < len(parsed_rows):
                parsed_row = parsed_rows[current_idx]
                is_off_policy = int(parsed_row[off_policy_index]) == 1
                if not is_off_policy and transition_set_count < database_size:
                    if parsed_row[action_index] == 1:
                        biased_database_includes_suppress_action = True
                    else:
                        biased_database_includes_letburn_action = True
                    write_row(parsed_row, file_references["biased"+str(database_size)])
                if transition_set_count < database_size:
                    write_row(parsed_row, file_references["unbiased"+str(database_size)])
                current_idx += 1
                if current_idx in starts_of_transition_sets:
                    break

    for f_ref in file_references.keys():
        file_references[f_ref].close()
    assert biased_database_includes_suppress_action and biased_database_includes_letburn_action


if __name__ == "__main__":
    #baseline()
    experiment()
    #produce_smaller_databases()