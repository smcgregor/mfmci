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

reward_function = reward_module.reward_factory({}) #  todo: specify the reward function from parameters

data = json.load(urllib2.urlopen(url))
total = reward_function(data)

# SMAC has a few different output fields; here, we only need the 4th output:
print "Result for SMAC: SUCCESS, 0, 0, {}, 0".format(total)
