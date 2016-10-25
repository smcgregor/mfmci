panel = {
            "panel_title": "Sampling Effort",
            "panel_icon": "glyphicon-retweet",
            "panel_description": "Define how many trajectories you want to generate, and to what time horizon.",
            "quantitative": [  # Real valued parameters
                               {
                                   "name": "Sample Count",
                                   "description": "Specify how many trajectories to generate",
                                   "current_value": 10,
                                   "max": 80,
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
                               },
                               {
                                   "name": "Render Ground Truth",
                                   "description": "Render the Monte Carlo trajectories instead of the MFMCi trajectories",
                                   "current_value": 0,
                                   "max": 1,
                                   "min": 0,
                                   "step": 1,
                                   "units": ""
                               }
            ],
            "categorical": [],
            "text": []
}
