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
                               }
            ],
            "categorical": [],
            "text": []
}
