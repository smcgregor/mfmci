"""
Test the testing domain, which is a database with 4 state transitions.
"""
from MFMCi import MFMCi
import sklearn


def test_insort_merge():
    """
    Test the insort merge function.
    """
    mfmci = MFMCi("testing")
    count = 0
    while count + 1 < len(mfmci.database):
        tuple_1 = mfmci.database[count]
        tuple_2 = mfmci.database[count + 1]
        for key1, result1 in tuple_1.results.iteritems():
            for key2, result2 in tuple_2.results.iteritems():
                assert result1["additional variables"]["time step"] <= result2["additional variables"]["time step"],\
                    "{} is not LEQ than {}".format(result1["additional variables"]["time step"], result2["additional variables"]["time step"])
                if result1["additional variables"]["time step"] == result2["additional variables"]["time step"]:
                    assert result1["additional variables"]["trajectory identifier"] <= result2["additional variables"]["trajectory identifier"]
                    if result1["additional variables"]["trajectory identifier"] == result2["additional variables"]["trajectory identifier"]:
                        assert result1["additional variables"]["policy identifier"] <= result2["additional variables"]["policy identifier"]
        count += 1


def test_initialization():
    """
    Test the initialization of the testing domain without creating trajectories.
    """
    mfmci = MFMCi("testing")
    assert mfmci.PRE_TRANSITION_VARIABLES == ["one start"]
    assert mfmci.POST_TRANSITION_VARIABLES == ["one end"]
    assert mfmci.STATE_SUMMARY_VARIABLES == ["action", "reward"]
    assert len(mfmci.POSSIBLE_ACTIONS) == 2

    assert mfmci.trajectory_set_counter == -1

    assert mfmci.distance_metric[0][0] == 4
    assert len(mfmci.distance_metric) == 1
    assert len(mfmci.distance_metric[0])

    assert type(mfmci.tree) == sklearn.neighbors.ball_tree.BinaryTree or \
        type(mfmci.tree) == sklearn.neighbors.ball_tree.BallTree, "Type: {}".format(type(mfmci.tree))

    assert len(mfmci.database) == 2
    for transition_set in mfmci.database:
        actions = transition_set.results.keys()
        assert len(transition_set.results) == 2
        assert 0.0 in actions
        assert 1.0 in actions


def test_ball_tree_queries():
    """
    Test the ball tree queries return the proper transition tuples.
    """
    mfmci = MFMCi("testing")
    assert type(mfmci.tree) == sklearn.neighbors.ball_tree.BinaryTree or \
        type(mfmci.tree) == sklearn.neighbors.ball_tree.BallTree, "Type: {}".format(type(mfmci.tree))
    mfmci.trajectory_set_counter += 1
    transition_set, distance = mfmci._get_closest_transition_set([10])
    assert transition_set[0] == 1.0, "transition_set[0] was {}".format(transition_set[0])
    assert distance == 18.0, "Distance was {}".format(distance)
    transition_set.last_accessed_iteration = mfmci.trajectory_set_counter
    transition_set, distance = mfmci._get_closest_transition_set([10])
    assert transition_set[0] == 0.0, "transition_set[0] was {}".format(transition_set[0])
    assert distance == 20.0, "Distance was {}".format(distance)
    try:
        transition_set.last_accessed_iteration = mfmci.trajectory_set_counter
        mfmci._get_closest_transition_set([10])
        assert False
    except Exception:
        print "Exception properly thrown since the database is exhausted"


def test_get_trajectories():
    """
    Test the construction of trajectories from the database.
    """
    def policy0(not_used):
        return 0

    def policy1(not_used):
        return 1

    mfmci = MFMCi("testing")
    trajectories = mfmci.get_trajectories(count=1,horizon=1,policy=policy0)
    assert len(trajectories) == 1
    assert len(trajectories[0]) == 1
    assert trajectories[0][0]["reward"] == 0.0
    assert trajectories[0][0]["action"] == 0.0

    trajectories = mfmci.get_trajectories(count=1,horizon=1,policy=policy1)
    assert len(trajectories) == 1
    assert len(trajectories[0]) == 1
    assert trajectories[0][0]["reward"] == 0.0
    assert trajectories[0][0]["action"] == 1.0

    trajectories = mfmci.get_trajectories(count=1,horizon=2,policy=policy1)
    assert len(trajectories) == 1
    assert len(trajectories[0]) == 2
    assert trajectories[0][0]["reward"] == 0.0
    assert trajectories[0][0]["action"] == 1.0
    assert trajectories[0][1]["reward"] == 0.0
    assert trajectories[0][1]["action"] == 1.0
