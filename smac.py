"""
This file bridges the MFMCi trajectory server with the SMAC Bayesian optimization library.
===================
For this script to work you will need to be running the Flask server on localhost:8000.
Otherwise the runtime for SMAC will be dominated by MFMCi's database load time.

Call this file from SMAC:

> ./smac --use-instances false --numberOfRunsLimit 100 --pcs-file ../mfmci/databases/wildfire/params.pcs --algo "python ../mfmci/smac.py" --run-objective QUALITY

todo: properly generalize this file to any domain in MFMCi.

See: http://www.cs.ubc.ca/labs/beta/Projects/SMAC/v2.10.03/quickstart.html

:copyright: (C) 2016 by Sean McGregor.
:license:   MIT, see LICENSE for more details.
"""
#!/usr/bin/python

import sys
import json
import urllib2
import importlib

# For black box function optimization, we can ignore the first 5 arguments.
# The remaining arguments specify parameters using this format: -name value

params = {}
for i in range(len(sys.argv)-1):
    if sys.argv[i][0] == '-':
        params[sys.argv[i].strip("-")] = sys.argv[i+1]

annotations = importlib.import_module("databases." + params["domain"] + ".annotate")
reward_module = importlib.import_module("databases." + params["domain"] + ".rewards")

params["sample_count"] = params["count"]
params["horizon"] = params["horizon"]
url = annotations.get_smac_url(params)


reward_sum = int(params["rewards_suppression"]) + int(params["rewards_timber"]) + int(params["rewards_ecology"]) + int(params["rewards_air"]) + int(params["rewards_recreation"])
reward_compontent = ""
if params["rewards_suppression"] == "1" and params["rewards_timber"] == "1" and params["rewards_ecology"] == "1" and params["rewards_air"] == "1" and params["rewards_recreation"] == "1":
    reward_compontent = "composite"
elif params["rewards_suppression"] == "0" and params["rewards_timber"] == "1" and params["rewards_ecology"] == "1" and params["rewards_air"] == "1" and params["rewards_recreation"] == "1":
    reward_compontent = "politics"
elif params["rewards_suppression"] == "0" and params["rewards_timber"] == "0" and params["rewards_ecology"] == "0" and params["rewards_air"] == "1" and params["rewards_recreation"] == "1":
    reward_compontent = "home"
elif params["rewards_suppression"] == "1" and params["rewards_timber"] == "1" and params["rewards_ecology"] == "0" and params["rewards_air"] == "0" and params["rewards_recreation"] == "0":
    reward_compontent = "timber"
elif params["rewards_suppression"] == "0" and params["rewards_timber"] == "0" and params["rewards_ecology"] == "0" and params["rewards_air"] == "1" and params["rewards_recreation"] == "0":
    reward_compontent = "air"
elif reward_sum == 1:
    if params["rewards_suppression"] == "1":
        reward_compontent = "suppression_expense_reward"
    elif params["rewards_timber"] == "1":
        reward_compontent = "harvest_reward"
    elif params["rewards_ecology"] == "1":
        reward_compontent = "restoration_index_reward"
    elif params["rewards_air"] == "1":
        reward_compontent = "airshed_reward"
    elif params["rewards_recreation"] == "1":
        reward_compontent = "recreation_index_reward"
    else:
        assert False
else:
    assert False

reward_function = reward_module.reward_factory({"component": reward_compontent})

data = json.load(urllib2.urlopen(url))
total = reward_function(data["trajectories"])

suppression_count = 0
for traj in data["trajectories"]:
    for time_step in traj:
        if time_step["action"] == 1:
            suppression_count += 1

with open("parameter_exploration" + reward_compontent + ".csv", "a") as f:

    f.write("{},".format(suppression_count))
    f.write("{},".format(total))

    f.write("{},".format(int(params["high_fuel_count"])))

    f.write("{},".format(int(params["fire_size_differential_1"])))
    f.write("{},".format(int(params["fire_size_differential_2"])))

    f.write("{},".format(int(params["fire_suppression_cost_1"])))
    f.write("{},".format(int(params["fire_suppression_cost_2"])))
    f.write("{},".format(int(params["fire_suppression_cost_3"])))
    f.write("{},".format(int(params["fire_suppression_cost_4"])))

    f.write("{},".format(int(params["fire_days_differential_1"])))
    f.write("{},".format(int(params["fire_days_differential_2"])))
    f.write("{},".format(int(params["fire_days_differential_3"])))
    f.write("{},".format(int(params["fire_days_differential_4"])))
    f.write("{},".format(int(params["fire_days_differential_5"])))
    f.write("{},".format(int(params["fire_days_differential_6"])))
    f.write("{},".format(int(params["fire_days_differential_7"])))
    f.write("{}".format(int(params["fire_days_differential_8"])))
    f.write("\n")


# SMAC has a few different output fields; here, we only need the 4th output:
print "Result for SMAC: SUCCESS, 0, 0, {}, 0".format(-total)
