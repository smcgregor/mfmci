# All the variables that are used in the distance metric
PRE_TRANSITION_VARIABLES = [
    "Fuel Model start", # \/ pulled from the landscape summary of the prior time step's onPolicy landscape
    "Canopy Closure start",
    "Canopy Height start",
    "Canopy Base Height start",
    "Canopy Bulk Density start",
    "Covertype start",
    "Stand Density Index start",
    "Succession Class start",
    "Maximum Time in State start",
    "Stand Volume Age start"
]

# The variables that correspond to the variables in PRE_TRANSITION_VARIABLES
POST_TRANSITION_VARIABLES = [
    "Fuel Model end", # \/ pulled from the landscape summary of the current row
    "Canopy Closure end",
    "Canopy Height end",
    "Canopy Base Height end",
    "Canopy Bulk Density end",
    "Covertype end",
    "Stand Density Index end",
    "Succession Class end",
    "Maximum Time in State end",
    "Stand Volume Age end"
]

# All the variables we visualize
STATE_SUMMARY_VARIABLES = [
    "action",
    "CrownFirePixels",
    "SurfaceFirePixels",
    "fireSuppressionCost",
    "timberLoss_IJWF",
    "boardFeetHarvestTotal",
    "boardFeetHarvestPonderosa",
    "boardFeetHarvestLodgepole",
    "boardFeetHarvestMixedConifer"
]

# All the actions that are possible
POSSIBLE_ACTIONS = [
    0,
    1
]

def PROCESS_ROW(additional_state):
    """
    Process the additional state to include the proper titles.
    :param additional_state:
    :return:
    """
    if "onPolicy" in additional_state["lcpFileName"]:
        additional_state["on policy"] = 1
    else:
        additional_state["on policy"] = 0
    additional_state["time step"] = additional_state["year"]
    additional_state["trajectory identifier"] = additional_state["initialFire"]
    additional_state["policy identifier"] = "{}-{}" \
        .format(additional_state["policyThresholdERC"], additional_state["policyThresholdDays"])
