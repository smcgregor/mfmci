panel = {
            "panel_title": "Optimization",
            "panel_icon": "glyphicon-king",
            "panel_description": "Define the parameters of the optimization algorithm.",
            "quantitative": [  # Real valued parameters
                               {
                                   "name": "Number of Runs Limit",
                                   "description": "The number of policy evaluations",
                                   "current_value": 10,
                                   "max": 40,
                                   "min": 1,
                                   "step": 1,
                                   "units": "Unitless"
                               },
                               {
                                   "name": "discount",
                                   "description": "The number of policy evaluations",
                                   "current_value": 0.96,
                                   "max": 1,
                                   "min": 0,
                                   "step": .01,
                                   "units": "Unitless"
                               },
                               {
                                   "name": "rewards_suppression",
                                   "description": "Include suppression expenses in the rewards",
                                   "current_value": 1,
                                   "max": 1,
                                   "min": 0,
                                   "step": 0,
                                   "units": "Boolean"
                               },
                               {
                                   "name": "rewards_timber",
                                   "description": "Include timber revenues in the rewards",
                                   "current_value": 1,
                                   "max": 1,
                                   "min": 0,
                                   "step": 0,
                                   "units": "Boolean"
                               },
                               {
                                   "name": "rewards_ecology",
                                   "description": "Include ecology in the rewards",
                                   "current_value": 1,
                                   "max": 1,
                                   "min": 0,
                                   "step": 0,
                                   "units": "Boolean"
                               },
                               {
                                   "name": "rewards_air",
                                   "description": "Include air quality in the rewards",
                                   "current_value": 1,
                                   "max": 1,
                                   "min": 0,
                                   "step": 0,
                                   "units": "Boolean"
                               },
                               {
                                   "name": "rewards_recreation",
                                   "description": "Include recreation in the rewards",
                                   "current_value": 1,
                                   "max": 1,
                                   "min": 0,
                                   "step": 0,
                                   "units": "Boolean"
                               }
            ],
            "categorical": [],
            "text": []
}
