import math
from PIL import Image
import StringIO
from struct import unpack
import bz2

#harvest_priority_rows = [119, 136, 159, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # use range(1, 174) to include all of them
#harvest_priority_rows = [119, 136, 159, 103, 167, 120, 22]
#harvest_priority_rows = [162, 164, 167, 170, 173, 158, 159, 160, 161, 165, 9, 169]
harvest_priority_rows = []

# Variables used in all the distance metrics
common_distance_variables = [
    #"Fuel Model",
    "Canopy Closure",
    "Canopy Height",
    "Canopy Base Height",
    "Canopy Bulk Density",
    #"Covertype",
    "Stand Density Index",
    #"Succession Class",
    #"Maximum Time in State",
    "Stand Volume Age",
    "highFuel",
    #"modFuel",
    #"lowFuel",
    "time step"
]

# Variables only used in the exogenous distance metrics
common_exogenous_variables = [
    "Precipitation",
    "MaxTemperature",
    "MinHumidity",
    "WindSpeed",
    "ignitionCovertype",
    "ignitionSlope",
    "startIndex",
    "ERC",
    "SC"
]

# All the variables that are used in the distance metric
PRE_TRANSITION_VARIABLES = [i + " start" for i in common_distance_variables]
harvest_summary_names_start = ["PriorityRow" + str(i) + " start" for i in harvest_priority_rows]
PRE_TRANSITION_VARIABLES += harvest_summary_names_start
PRE_TRANSITION_EXOGENOUS_VARIABLES = PRE_TRANSITION_VARIABLES + [i + " start" for i in common_exogenous_variables]

# The variables that correspond to the variables in PRE_TRANSITION_VARIABLES
POST_TRANSITION_VARIABLES = [i + " end" for i in common_distance_variables]
harvest_summary_names_end = ["PriorityRow" + str(i) + " end" for i in harvest_priority_rows]
POST_TRANSITION_VARIABLES += harvest_summary_names_end

# The variables that correspond to the variables in PRE_TRANSITION_VARIABLES
POST_TRANSITION_EXOGENOUS_VARIABLES = POST_TRANSITION_VARIABLES + [i + " end" for i in common_exogenous_variables]

# All the variables we visualize
OBJECTIVE_VARIABLES = [
    "CrownFirePixels",
    "SurfaceFirePixels",
    "fireSuppressionCost",
    "boardFeetHarvestPonderosa",
    "boardFeetHarvestLodgepole",
    "boardFeetHarvestMixedConifer",
    "ponderosaSC1",
    "ponderosaSC2",
    "ponderosaSC3",
    "ponderosaSC4",
    "ponderosaSC5",
    "mixedConSC1",
    "mixedConSC2",
    "mixedConSC3",
    "mixedConSC4",
    "mixedConSC5",
    "lodgepoleSC1",
    "lodgepoleSC2",
    "lodgepoleSC3"
]

# How far in the future should we expect to have results
OBJECTIVE_HORIZON = 99

# The number of trajectories to generate in evaluating the quantile
OBJECTIVE_TRAJECTORY_COUNT = 30

# All the variables we visualize
VISUALIZATION_VARIABLES = [
    "on policy",
    "time step",
    "stitched policy ERC",
    "stitched policy Days",
    "on policy",
    "percentHighFuel start",
    #"offPolicy",
    "action",
    "CrownFirePixels",
    "SurfaceFirePixels",
    "fireSuppressionCost",
    "timberLoss_IJWF",
    #"boardFeetHarvestTotal",
    "boardFeetHarvestPonderosa",
    "boardFeetHarvestLodgepole",
    "boardFeetHarvestMixedConifer",
    "ponderosaSC1",
    "ponderosaSC2",
    "ponderosaSC3",
    "ponderosaSC4",
    "ponderosaSC5",
    "mixedConSC1",
    "mixedConSC2",
    "mixedConSC3",
    "mixedConSC4",
    "mixedConSC5",
    "lodgepoleSC1",
    "lodgepoleSC2",
    "lodgepoleSC3"
]
VISUALIZATION_VARIABLES = VISUALIZATION_VARIABLES + ["PriorityRow" + str(i) + " start" for i in range(1, 174)]

# All the actions that are possible
POSSIBLE_ACTIONS = [
    0,
    1
]

def write_smac_parameters(params):
    """
    Write the .pcs file as expected by the SMAC optimization library.
    :param params:
    :return:
    """
    erc_threshold = int(params["ERC Threshold"])
    days_threshold = int(params["Days Until End of Season Threshold"])

    # Write SMAC's parameter file
    f = open("smac.pcs", "w")
    f.write("erc integer [0,95] [{}]\n".format(erc_threshold))
    f.write("days integer [0,180] [{}]\n".format(days_threshold))
    f.close()

def get_smac_url(params):
    """
    Get the URL of the MFMCi server for the wildfire domain's trajectories as currently parameterized.
    :param params:
    :return:
    """
    return "http://localhost:8938/trajectories?Sample+Count=" + str(params["sample_count"]) + \
           "&Render+Ground+Truth=0" + \
           "&Use+Location+Policy=0" + \
           "&Use+Landscape+Policy=0" + \
           "&Horizon=" + str(params["horizon"]) + \
           "&ERC+Threshold=" + str(params["erc"]) + \
           "&Days+Until+End+of+Season+Threshold=" + str(params["days"])

def post_process_smac_output(last_row):
    """
    Post process the last line from the output of SMAC's output file to get the update policy parameters.
    These will be sent back to MDPvis.
    :return:
    """
    # An example output line is below
    # 5: days='56', erc='17'
    ret_params = {
        "ERC Threshold": last_row["erc"],
        "Days Until End of Season Threshold": last_row["days"],
        }
    return ret_params

def reward_function(data):
    """
    Calculate the rewards for the trajectories.
    todo: set the parameters of the reward function from the visualization.
    :param data:
    :return:
    """
    restoration_index_dollars = 1.0
    ponderosa_price_per_bf = 1.0
    mixed_conifer_price_per_bf = 1.0
    lodgepole_price_per_bf = 1.0

    # Real values
    restoration_index_targets = {
        "ponderosaSC1": 10,
        "ponderosaSC2": 5,
        "ponderosaSC3": 35,
        "ponderosaSC4": 45,
        "ponderosaSC5": 5#,
        #"mixedConSC1": 10, # We don't care about the RI of the non-pondersoa species
        #"mixedConSC2": 5,
        #"mixedConSC3": 30,
        #"mixedConSC4": 45,
        #"mixedConSC5": 10,
        #"lodgepoleSC1": 25,
        #"lodgepoleSC2": 55,
        #"lodgepoleSC3": 20
    }


    def compute_restoration_index(time_step):
        """
        Compute the squared deviation from the targets for the succession classes.
        """
        total = 0.0
        for k in restoration_index_targets:
            total += math.pow(restoration_index_targets[k] - time_step[k], 2)
        return total

    harvest_total = 0
    restoration_index_total = 0.0
    for trajectory in data["trajectories"]:
        for time_step in trajectory:
            restoration_index_total += compute_restoration_index(time_step) * restoration_index_dollars
            #harvest_total +=  # todo: incorporate harvest totals
    total = -(harvest_total + restoration_index_total)
    return total

def get_image(image_file_name):
    """
    Get the image of a compressed landscapes.
    :param name:
    :return: Returns an image IO object for streaming to the client.
    """
    # Layers:
    # 0: fuel
    # 1: canopyClosure
    # 2: canopyHeight
    # 3: canopyBaseHeight
    # 4: canopyBulkDensity
    # 5: coverIn
    # 6: standDensityIn
    # 7: successionClassIn
    # 8: maxTimeInState
    # 9: standVolumeAgeIn
    # 10: garbage

    # lcp_INITIALEVENT_CURRENTEVENT_ACTION_ERC_DAYS_onPolicy.lcp
    # lcp_INITIALEVENT_CURRENTEVENT_ACTION_ERC_DAYS_offPolicy.lcp
    layer, initial_fire, year, action, policy_threshold_erc, policy_threshold_days, on_policy = image_file_name.split("-")
    layer = int(layer)
    if int(on_policy) == 1:
        policy_label = "onPolicy"
    else:
        policy_label = "offPolicy"
    image_path = "databases/wildfire/warning_many_files/landscapes/lcp_{}_{}_{}_{}_{}_{}.lcp.bz2".format(
        int(float(initial_fire)),
        int(float(year)),
        int(float(action)),
        int(float(policy_threshold_erc)),
        int(float(policy_threshold_days)),
        policy_label
    )
    lcp_file = bz2.BZ2File(image_path, "r")
    print "processing %s" % image_path

    # Construct each of the layers found in the LCP
    layers = []
    for idx in range(0,11):
        layers.append([])

    short_count = 0 # 0 to 10,593,800
    short_bytes = lcp_file.read(2)
    while short_bytes != "":
        pix = unpack("<h", short_bytes)  # Unpack a single pixel
        layers[short_count % len(layers)].append(pix[0])  # Load the pixel into the layer
        short_count += 1 #  Pixel count, used to select layer
        short_bytes = lcp_file.read(2)  # Read the next pixel
    lcp_file.close()
    img = Image.new('RGB', (1127, 940), "white")
    img.putdata(layers[layer])
    img_io = StringIO.StringIO()
    img.save(img_io, 'JPEG', quality=100)
    img_io.seek(0)
    return img_io


def PROCESS_ROW(additional_state):
    """
    Process the additional state to include the proper titles and a list of the images for the /state endpoint.
    :param additional_state:
    :return:
    """
    additional_state["on policy"] = additional_state["onPolicy"]
    additional_state["time step"] = additional_state["year"]
    additional_state["time step start"] = additional_state["year"]
    additional_state["time step end"] = int(additional_state["year"]) + 1
    additional_state["trajectory identifier"] = additional_state["initialFire"]

    if "../landscapes/lcp_" in additional_state["lcpFileName"]:
        policy_parameters = additional_state["lcpFileName"].split("_")[4:6]
        policy_parameter_erc = policy_parameters[0]
        policy_parameter_day = policy_parameters[1]
    else:
        policy_parameter_erc = 0.0
        policy_parameter_day = 0.0
    additional_state["stitched policy ERC"] = float(policy_parameter_erc)
    additional_state["stitched policy Days"] = float(policy_parameter_day)
    additional_state["policy identifier"] = "{}-{}" \
        .format(policy_parameter_erc, policy_parameter_day)

    # Layers:
    # 0: fuel
    # 1: canopyClosure
    # 2: canopyHeight
    # 3: canopyBaseHeight
    # 4: canopyBulkDensity
    # 5: coverIn
    # 6: standDensityIn
    # 7: successionClassIn
    # 8: maxTimeInState
    # 9: standVolumeAgeIn
    # 10: garbage
    # Filename convention:
    #   lcp_INITIALEVENT_CURRENTEVENT_ACTION_ERC_DAYS_onPolicy.lcp
    #   lcp_INITIALEVENT_CURRENTEVENT_ACTION_ERC_DAYS_offPolicy.lcp
    additional_state["image row"] = []
    for layer in [0]:
        file_name = "{}-{}".format(layer,
                                   additional_state["lcpFileName"] # todo: update this for the new database
                                  )
        additional_state["image row"].append(file_name)

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
            "panel_title": "Optimization",
            "panel_icon": "glyphicon-king",
            "panel_description": "Define the parameters of the optimization algorithm.",
            "default_rendering": "radar", # Default to a radar plot. User can switch to input elements.
            "quantitative": [  # Real valued parameters
                               {
                                   "name": "Number of Runs Limit",
                                   "description": "The number of policy evaluations",
                                   "current_value": 10,
                                   "max": 40,
                                   "min": 1,
                                   "step": 1,
                                   "units": "Unitless"
                               }
            ]
        },
        {
            "panel_title": "Policy",
            "panel_icon": "glyphicon-random",
            "panel_description": "Define the parameters of the policies used to generate trajectories.",
            "default_rendering": "radar", # Default to a radar plot. User can switch to input elements.
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
            "categorical": [  # Discrete valued parameters, uses drop down or radar buttons for selection
                              {"Policy Class": ["severity", "location"]}
            ]
        }
    ]
}
