"""
Test the wildfire domain, which is a large database with many columns.
"""
from MFMCi import MFMCi
import csv
import bz2


def test_tuple_equality():
    """
    Confirm that the tuples in the database are equal to themselves.
    """
    mfmci = MFMCi("wildfire")
    end = len(mfmci.database)
    count = 0
    while count < end:
        tuple1 = mfmci.database[count]
        tuple_1_result_set_additional_variables = tuple1.results[tuple1.results.keys()[0]]["additional variables"]
        assert tuple1.eq(tuple1,
                         tuple_1_result_set_additional_variables["time step"],
                         tuple_1_result_set_additional_variables["trajectory identifier"],
                         tuple_1_result_set_additional_variables["policy identifier"]), \
            "Database entry {} did not test as being equal to itself".format(count)
        assert not tuple1.eq(tuple1,
                         tuple_1_result_set_additional_variables["time step"] + 1,
                         tuple_1_result_set_additional_variables["trajectory identifier"],
                         tuple_1_result_set_additional_variables["policy identifier"]), \
            "Database entry {} tested as being equal to a difference".format(count)
        assert not tuple1.eq(tuple1,
                             tuple_1_result_set_additional_variables["time step"],
                             tuple_1_result_set_additional_variables["trajectory identifier"] + 1,
                             tuple_1_result_set_additional_variables["policy identifier"]), \
            "Database entry {} tested as being equal to a difference".format(count)
        assert not tuple1.eq(tuple1,
                             tuple_1_result_set_additional_variables["time step"],
                             tuple_1_result_set_additional_variables["trajectory identifier"],
                             tuple_1_result_set_additional_variables["policy identifier"] + str(1)), \
            "Database entry {} tested as being equal to a difference".format(count)

        count += 1


def test_database_sorted():
    """
    Check that all the database's entries are sorted according to the tuple comparison.
    """
    mfmci = MFMCi("wildfire")
    end = len(mfmci.database)
    count = 0
    while count + 1 < end:
        tuple1 = mfmci.database[count]
        tuple2 = mfmci.database[count+1]
        #assert tuple1.has_all_actions(), "Count: {}".format(count)
        #assert tuple2.has_all_actions(), "Count: {}".format(count)
        tuple_2_result_set_additional_variables = tuple2.results[tuple2.results.keys()[0]]["additional variables"]
        assert tuple1.less_than(tuple1,
                                tuple_2_result_set_additional_variables["time step"],
                                tuple_2_result_set_additional_variables["trajectory identifier"],
                                tuple_2_result_set_additional_variables["policy identifier"]),\
            "Database entry {}".format(count)
        count += 1


def test_database_transition_tuples_are_complete():
    """
    Check all the transitions in the wildfire database to ensure they are complete.
    """
    mfmci = MFMCi("wildfire")
    assert len(mfmci.POSSIBLE_ACTIONS) == 2
    count = 0
    for tuple in mfmci.database:
        if tuple.has_all_actions():
            count += 1
        assert tuple.has_all_actions(), "{}--{}--{}".format(tuple, tuple.results, tuple.results.keys())


def test_check_csv():
    """
    Confirm that all the transitions in the database are paired.
    :return:
    """
    actionIndex = 41
    yearIndex = 42
    initialFireIndex = 40
    policyThresholdERCIndex = 58
    policyThresholdDaysIndex = 59

    with bz2.BZ2File("databases/wildfire/database.csv.bz2", 'rb') as csv_file:
        transitions = csv.reader(csv_file, delimiter=',')
        transitions.next() # discard header
        count = 0.0
        try:
            while True:
                row1 = transitions.next()
                count += 1.0
                row2 = transitions.next()
                count += 1.0
                assert row1[actionIndex] != row2[actionIndex]
                assert row1[yearIndex] == row2[yearIndex], "{}:::{}--{}".format(row1[yearIndex], row2[yearIndex], count)
                assert row1[initialFireIndex] == row2[initialFireIndex], "{}:::{}--{}".format(row1[initialFireIndex], row2[initialFireIndex], count)
                assert "{}-{}" \
                               .format(int(row1[policyThresholdERCIndex]),
                                       int(row1[policyThresholdDaysIndex])) == "{}-{}" \
                        .format(int(row2[policyThresholdERCIndex]),
                                int(row2[policyThresholdDaysIndex]))
        except StopIteration:
            print "completed iteration on row: {}".format(count)
            assert count == 153252.0