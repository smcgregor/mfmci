"""
Test the wildfire domain, which is a large database with many columns.
"""
from MFMCi import MFMCi


def test_initialization():
    """
    Test the initialization of the testing domain without creating trajectories.
    """
    mfmci = MFMCi("wildfire")
    assert len(mfmci.POSSIBLE_ACTIONS) == 2
