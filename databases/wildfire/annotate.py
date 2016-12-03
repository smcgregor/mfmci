import math
from PIL import Image
import StringIO
import importlib
import glob
from struct import unpack
import bz2
import databases.wildfire.rewards

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
    "lodgepoleSC3",
    "startIndex",
    "endIndex",

    "rewards all",
    "rewards restoration",
    "rewards harvest",
    "rewards airshed",
    "rewards recreation",
    "rewards suppression"
]
#VISUALIZATION_VARIABLES = VISUALIZATION_VARIABLES + ["PriorityRow" + str(i) + " start" for i in range(1, 174)]

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
    if False:
        f.write("high_fuel_count integer [0,1000000] [{}]\n".format(int(params["high_fuel_count"])))

        f.write("fire_size_differential_1 integer [0,1000000] [{}]\n".format(int(params["fire_size_differential_1"])))
        f.write("fire_size_differential_2 integer [0,1000000] [{}]\n".format(int(params["fire_size_differential_2"])))

        f.write("fire_suppression_cost_1 integer [0,10000000] [{}]\n".format(int(params["fire_suppression_cost_1"])))
        f.write("fire_suppression_cost_2 integer [0,10000000] [{}]\n".format(int(params["fire_suppression_cost_2"])))
        f.write("fire_suppression_cost_3 integer [0,10000000] [{}]\n".format(int(params["fire_suppression_cost_3"])))
        f.write("fire_suppression_cost_4 integer [0,10000000] [{}]\n".format(int(params["fire_suppression_cost_4"])))

        f.write("fire_days_differential_1 integer [0,60] [{}]\n".format(int(params["fire_days_differential_1"])))
        f.write("fire_days_differential_2 integer [0,60] [{}]\n".format(int(params["fire_days_differential_2"])))
        f.write("fire_days_differential_3 integer [0,60] [{}]\n".format(int(params["fire_days_differential_3"])))
        f.write("fire_days_differential_4 integer [0,60] [{}]\n".format(int(params["fire_days_differential_4"])))
        f.write("fire_days_differential_5 integer [0,60] [{}]\n".format(int(params["fire_days_differential_5"])))
        f.write("fire_days_differential_6 integer [0,60] [{}]\n".format(int(params["fire_days_differential_6"])))
        f.write("fire_days_differential_7 integer [0,60] [{}]\n".format(int(params["fire_days_differential_7"])))
        f.write("fire_days_differential_8 integer [0,60] [{}]\n".format(int(params["fire_days_differential_8"])))
    else:
        f.write("high_fuel_count_1 integer [0,1000000] [{}]\n".format(int(params["high_fuel_count_1"])))
        f.write("high_fuel_count_2 integer [0,1000000] [{}]\n".format(int(params["high_fuel_count_2"])))

        f.write("erc_1 integer [0,100] [{}]\n".format(int(params["erc_1"])))
        f.write("erc_2 integer [0,100] [{}]\n".format(int(params["erc_2"])))
        f.write("erc_3 integer [0,100] [{}]\n".format(int(params["erc_3"])))
        f.write("erc_4 integer [0,100] [{}]\n".format(int(params["erc_4"])))

        f.write("day_1 integer [0,180] [{}]\n".format(int(params["day_1"])))
        f.write("day_2 integer [0,180] [{}]\n".format(int(params["day_2"])))
        f.write("day_3 integer [0,180] [{}]\n".format(int(params["day_3"])))
        f.write("day_4 integer [0,180] [{}]\n".format(int(params["day_4"])))
        f.write("day_5 integer [0,180] [{}]\n".format(int(params["day_5"])))
        f.write("day_6 integer [0,180] [{}]\n".format(int(params["day_6"])))
        f.write("day_7 integer [0,180] [{}]\n".format(int(params["day_7"])))
        f.write("day_8 integer [0,180] [{}]\n".format(int(params["day_8"])))
    f.close()

def get_smac_url(params):
    """
    Get the URL of the MFMCi server for the wildfire domain's trajectories as currently parameterized.
    :param params:
    :return:
    """
    if False:
        return "http://localhost:8938/trajectories?Sample+Count=" + str(params["sample_count"]) + \
               "&Render+Ground+Truth=0" + \
               "&Use+Location+Policy=0" + \
               "&Use+Landscape+Policy=0" + \
               "&Use+Tree+Policy=1" + \
               "&Horizon=" + str(params["horizon"]) + \
               "&high_fuel_count=" + str(params["high_fuel_count"]) + \
               "&fire_size_differential_1=" + str(params["fire_size_differential_1"]) + \
               "&fire_size_differential_2=" + str(params["fire_size_differential_2"]) + \
               "&fire_suppression_cost_1=" + str(params["fire_suppression_cost_1"]) + \
               "&fire_suppression_cost_2=" + str(params["fire_suppression_cost_2"]) + \
               "&fire_suppression_cost_3=" + str(params["fire_suppression_cost_3"]) + \
               "&fire_suppression_cost_4=" + str(params["fire_suppression_cost_4"]) + \
               "&fire_days_differential_1=" + str(params["fire_days_differential_1"]) + \
               "&fire_days_differential_2=" + str(params["fire_days_differential_2"]) + \
               "&fire_days_differential_3=" + str(params["fire_days_differential_3"]) + \
               "&fire_days_differential_4=" + str(params["fire_days_differential_4"]) + \
               "&fire_days_differential_5=" + str(params["fire_days_differential_5"]) + \
               "&fire_days_differential_6=" + str(params["fire_days_differential_6"]) + \
               "&fire_days_differential_7=" + str(params["fire_days_differential_7"]) + \
               "&fire_days_differential_8=" + str(params["fire_days_differential_8"]) + \
               "&ERC+Threshold=" + str(0) + \
               "&Days+Until+End+of+Season+Threshold=" + str(0)
               #"&ERC+Threshold=" + str(params["erc"]) + \
               #"&Days+Until+End+of+Season+Threshold=" + str(params["days"])
    else:
        return "http://localhost:8938/trajectories?Sample+Count=" + str(params["sample_count"]) + \
               "&Render+Ground+Truth=0" + \
               "&Use+Location+Policy=0" + \
               "&Use+Landscape+Policy=0" + \
               "&Use+Tree+Policy=1" + \
               "&Horizon=" + str(params["horizon"]) + \
               "&high_fuel_count_1=" + str(params["high_fuel_count_1"]) + \
               "&high_fuel_count_2=" + str(params["high_fuel_count_2"]) + \
               "&erc_1=" + str(params["erc_1"]) + \
               "&erc_2=" + str(params["erc_2"]) + \
               "&erc_3=" + str(params["erc_3"]) + \
               "&erc_4=" + str(params["erc_4"]) + \
               "&day_1=" + str(params["day_1"]) + \
               "&day_2=" + str(params["day_2"]) + \
               "&day_3=" + str(params["day_3"]) + \
               "&day_4=" + str(params["day_4"]) + \
               "&day_5=" + str(params["day_5"]) + \
               "&day_6=" + str(params["day_6"]) + \
               "&day_7=" + str(params["day_7"]) + \
               "&day_8=" + str(params["day_8"]) + \
               "&ERC+Threshold=" + str(0) + \
               "&Days+Until+End+of+Season+Threshold=" + str(0)
        #"&ERC+Threshold=" + str(params["erc"]) + \
        #"&Days+Until+End+of+Season+Threshold=" + str(params["days"])

def post_process_smac_output(last_row):
    """
    Post process the last line from the output of SMAC's output file to get the update policy parameters.
    These will be sent back to MDPvis.
    :return:
    """
    # An example output line is below
    # 5: days='56', erc='17'
    #ret_params = {
    #    "ERC Threshold": last_row["erc"],
    #    "Days Until End of Season Threshold": last_row["days"],
    #    }
    if False:
        ret_params = {
            "high_fuel_count": last_row["high_fuel_count"],
            "fire_size_differential_1": last_row["fire_size_differential_1"],
            "fire_size_differential_2": last_row["fire_size_differential_2"],
            "fire_suppression_cost_1": last_row["fire_suppression_cost_1"],
            "fire_suppression_cost_2": last_row["fire_suppression_cost_2"],
            "fire_suppression_cost_3": last_row["fire_suppression_cost_3"],
            "fire_suppression_cost_4": last_row["fire_suppression_cost_4"],
            "fire_days_differential_1": last_row["fire_days_differential_1"],
            "fire_days_differential_2": last_row["fire_days_differential_2"],
            "fire_days_differential_3": last_row["fire_days_differential_3"],
            "fire_days_differential_4": last_row["fire_days_differential_4"],
            "fire_days_differential_5": last_row["fire_days_differential_5"],
            "fire_days_differential_6": last_row["fire_days_differential_6"],
            "fire_days_differential_7": last_row["fire_days_differential_7"],
            "fire_days_differential_8": last_row["fire_days_differential_8"]
            }
        return ret_params
    else:
        ret_params = {
            "high_fuel_count_1": last_row["high_fuel_count_1"],
            "high_fuel_count_2": last_row["high_fuel_count_2"],
            "erc_1": last_row["erc_1"],
            "erc_2": last_row["erc_2"],
            "erc_3": last_row["erc_3"],
            "erc_4": last_row["erc_4"],
            "day_1": last_row["day_1"],
            "day_2": last_row["day_2"],
            "day_3": last_row["day_3"],
            "day_4": last_row["day_4"],
            "day_5": last_row["day_5"],
            "day_6": last_row["day_6"],
            "day_7": last_row["day_7"],
            "day_8": last_row["day_8"]
        }
    return ret_params


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


all_rewards = databases.wildfire.rewards.reward_factory({"component": "all"})
restoration_rewards = databases.wildfire.rewards.reward_factory({"component": "restoration_index_reward"})
harvest_rewards = databases.wildfire.rewards.reward_factory({"component": "harvest_reward"})
airshed_rewards = databases.wildfire.rewards.reward_factory({"component": "airshed_reward"})
recreation_rewards = databases.wildfire.rewards.reward_factory({"component": "recreation_index_reward"})
suppression_rewards = databases.wildfire.rewards.reward_factory({"component": "suppression_expense_reward"})

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

    additional_state["rewards all"] = all_rewards(additional_state)
    additional_state["rewards restoration"] = restoration_rewards(additional_state)
    additional_state["rewards harvest"] = harvest_rewards(additional_state)
    additional_state["rewards airshed"] = airshed_rewards(additional_state)
    additional_state["rewards recreation"] = recreation_rewards(additional_state)
    additional_state["rewards suppression"] = suppression_rewards(additional_state)

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
    }
}
mdpvis_initialization_object["parameter_collections"] = []
panel_files = glob.glob("databases/wildfire/panels/*.py")
for panel_file in panel_files:
    panel_file = panel_file.split("/")[-1]
    if panel_file == "__init__.py":
        continue
    pf = panel_file.split(".")[0]
    panel_module = importlib.import_module("databases.wildfire.panels." + pf)
    mdpvis_initialization_object["parameter_collections"].append(panel_module.panel)
