panel = {
            "panel_title": "Policy",
            "panel_icon": "glyphicon-random",
            "panel_description": "Define the parameters of the policies used to generate trajectories.",
            "quantitative": [  # Real valued parameters
                {
                    "name": "Use Location Policy",
                    "description": "Use a policy that splits the landscape geographically",
                    "current_value": 0,
                    "max": 1,
                    "min": 0,
                    "step": 1,
                    "units": "boolean"
                },
                {
                    "name": "Use Landscape Policy",
                    "description": "Use a policy based on the total fuels on the landscape",
                    "current_value": 0,
                    "max": 1,
                    "min": 0,
                    "step": 1,
                    "units": "boolean"
                },
                {
                    "name": "ERC Threshold",
                    "description": "Values of Energy Release Component greater than " +
                                   "this parameter will be suppressed (up to the value of 95)",
                    "current_value": 65,
                    "max": 95,
                    "min": 0,
                    "step": 1,
                    "units": "Unitless"
                },
                {
                    "name": "Days Until End of Season Threshold",
                    "description": "Values of Ignition Day less than this parameter will " +
                                   "be suppressed if the ERC parameter is in the suppressable range",
                    "current_value": 100,
                    "max": 180,
                    "min": 0,
                    "step": 1,
                    "units": "Days"
                }
            ],
            "categorical": [],
            "text": []
}
