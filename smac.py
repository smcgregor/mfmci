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
import math

# For black box function optimization, we can ignore the first 5 arguments.
# The remaining arguments specify parameters using this format: -name value

days = 0
erc = 0

for i in range(len(sys.argv)-1):
    if sys.argv[i] == '-days':
        days = int(sys.argv[i+1])
    elif sys.argv[i] == '-erc':
        erc = int(sys.argv[i+1])
sample_count = 30
horizon = 100
url = "http://localhost:8938/trajectories?Sample+Count=" + str(sample_count) +\
      "&Horizon=" + str(horizon) + "&ERC+Threshold=" + str(erc) + "&Days+Until+End+of+Season+Threshold=" + str(days)

data = json.load(urllib2.urlopen(url))

# todo: Parameters we will want to set in the visualization
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
    "ponderosaSC5": 5,
    "mixedConSC1": 10,
    "mixedConSC2": 5,
    "mixedConSC3": 30,
    "mixedConSC4": 45,
    "mixedConSC5": 10,
    "lodgepoleSC1": 25,
    "lodgepoleSC2": 55,
    "lodgepoleSC3": 20
}


def compute_restoration_index(time_step):
    total = 0.0
    for k in restoration_index_targets:
        total += math.pow(restoration_index_targets[k] - time_step[k], 2)
    return total

# todo: this gives innordinate weight to mixedCon, no?
harvest_total = 0
restoration_index_total = 0.0
for trajectory in data["trajectories"]:
    for time_step in trajectory:
        restoration_index_total += compute_restoration_index(time_step) * restoration_index_dollars
        #harvest_total +=  # todo


total = -(harvest_total + restoration_index_total)

# SMAC has a few different output fields; here, we only need the 4th output:
print "Result for SMAC: SUCCESS, 0, 0, {}, 0".format(total)
