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

# The initialization object for MDPvis
mdpvis_initialization_object = {

    # The settings to apply at initialization time
    "mdpvis_settings": {
        "domain_instructions": "todo",
        "domain_cover_image": "todo",
        "saved states": [
            {
                "description": "A set of interesting queries",
                "href": "todo"
            }
        ]
    },

    # The control panels that appear at the top of the screen
    "parameter_collections": [
        {
            "panel_title": "Policy",
            "panel_icon": "glyphicon-random",
            "panel_description": "Define the parameters of the policies used to generate trajectories.",
            "default_rendering": "radar", # Default to a radar plot. User can switch to input elements.
            "quantitative": [  # Real valued parameters
                {
                    "name": "ERC Threshold",
                    "description": "Values of Energy Release Component greater than " +
                                   "this parameter will be suppressed (up to the value of 95)",
                    "current_value": 0,
                    "max": 95,
                    "min": 0,
                    "step": 1,
                    "units": "Unitless"
                },
                {
                    "name": "Days Until End of Season Threshold",
                    "description": "Values of Ignition Day less than this parameter will " +
                                   "be suppressed if the ERC parameter is in the suppressable range",
                    "current_value": 0,
                    "max": 180,
                    "min": 0,
                    "step": 1,
                    "units": "Days"
                }
            ],
            "categorical": [  # Discrete valued parameters, uses drop down or radar buttons for selection
                              {"Policy Class": ["severity", "location"]}
            ]
        },
        {
            "panel_title": "Sampling Effort",
            "panel_icon": "glyphicon-retweet",
            "panel_description": "Define how many trajectories you want to generate, and to what time horizon.",
            "default_rendering": "radar", # Default to a radar plot. User can switch to input elements.
            "quantitative": [  # Real valued parameters
                               {
                                   "name": "Sample Count",
                                   "description": "Specify how many trajectories to generate",
                                   "current_value": 10,
                                   "max": 1000,
                                   "min": 1,
                                   "step": 1,
                                   "units": "#"
                               },
                               {
                                   "name": "Horizon",
                                   "description": "The time step at which simulation terminates",
                                   "current_value": 10,
                                   "max": 100,
                                   "min": 1,
                                   "step": 1,
                                   "units": "Years"
                               }
            ],
            "categorical": [  # Discrete valued parameters, uses drop down or radar buttons for selection
                              {"Policy Class": ["severity", "location"]}
            ]
        }
    ]

}
