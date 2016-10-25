panel = {
            "panel_title": "Rewards",
            "panel_icon": "glyphicon-random",
            "panel_description": "Define the parameters of the reward function.",
            "quantitative": [  # Real valued parameters
                {
                    "name": "restoration index dollars",
                    "description": "The scalar applied to the restoration index to assess economic value for ecology",
                    "current_value": 0,
                    "max": 1000000000,
                    "min": 0,
                    "step": 1000,
                    "units": "$"
                },
                {
                    "name": "ponderosa price per bf",
                    "description": "The price received per board foot of ponderosa lumber",
                    "current_value": 0,
                    "max": 1000,
                    "min": 0,
                    "step": 1,
                    "units": "$"
                },
                {
                   "name": "mixed conifer price per bf",
                   "description": "The price received per board foot of mixed conifer lumber",
                   "current_value": 0,
                   "max": 1000,
                   "min": 0,
                   "step": 1,
                   "units": "$"
                },
                {
                   "name": "lodgepole price per bf",
                   "description": "The price received per board foot of lodgepole lumber",
                   "current_value": 0,
                   "max": 1000,
                   "min": 0,
                   "step": 1,
                   "units": "$"
                },
                {
                   "name": "airshed smoke reward per day",
                   "description": "The price per day of smoke",
                   "current_value": 0,
                   "max": 1000000,
                   "min": 0,
                   "step": 100,
                   "units": "$"
                },
                {
                   "name": "recreation index dollars",
                   "description": "The scalar weight on the recreation index",
                   "current_value": 0,
                   "max": 1000000,
                   "min": 0,
                   "step": 100,
                   "units": "$"
                },
                {
                   "name": "suppression expense dollars",
                   "description": "The scalar applied to the suppression expenses",
                   "current_value": 1,
                   "max": 1000,
                   "min": -1000,
                   "step": 1,
                   "units": "NA"
                },
            ],
            "categorical": [],
            "text": []
}
