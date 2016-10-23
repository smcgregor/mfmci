import os
import pickle
import nose.tools
import bz2
import random
import csv
import array
"""
Post process runs from wildfire simulator in order to build and evaluate databases. This script is
for a specific workflow and should not be applied to other systems, simulators, clusters, etc.

Step 1: ssh into the high performance cluster

Step 2: Copy the raw outputs and process them into a CSV

cd /nfs/eecs-fserv/share/mcgregse/tmp
cp /scratch/eecs-share/rhoutman/FireWoman/results/estimatedpolicy-* .
grep CSVROWFORPARSER estimatedpolicy-HIGH_FUEL_POLICY-i-[3-6][0-9].out -h | sed 's/^.................//' > ../databases/fuel_raw_policy.csv
grep CSVROWFORPARSER estimatedpolicy-SPLIT_LANDSCAPE_POLICY-i-[0-3][0-9].out -h | sed 's/^.................//' > ../databases/location_raw_policy.csv
grep CSVROWFORPARSER estimatedpolicy-IGNITION_POLICY-i-*-erc-65-days-100.out -h | sed 's/^.................//' > ../databases/intensity_raw_policy.csv
grep CSVROWFORPARSER estimatedpolicy-IGNITION_POLICY-i-1-erc-*-days-*.out -h | sed 's/^.................//' > ../databases/raw_database.csv

Step 3: Post-process all the landscapes

cd ../mfmci/
./cluster_nosetest.sh post_process.py:test_post_process_landscapes

/nfs/guille/tgd/users/mcgregse/anaconda2/bin/nosetests post_process.py:test_post_process_landscapes -s

Step 4: Confirm that all the landscape summaries have been built

/nfs/guille/tgd/users/mcgregse/anaconda2/bin/nosetests post_process.py:test_check_for_incomplete_pickles -s

Step 5: Process the output files to include the landscape summaries

./cluster_nosetest.sh post_process.py:test_process_raw_output

or

/nfs/guille/tgd/users/mcgregse/anaconda2/bin/nosetests post_process.py:test_process_raw_output -s

"""


def pad_string(s, l=4):
    """
    s: the string to pad
    l: the length to pad to
    """
    while len(s) < l:
        s += "p"
    return s


def getRowIDs():
    harvestVolumes = open("databases/wildfire/harvestVolumeList.txt", "r")
    rowIDs = {}
    for idx, line in enumerate(harvestVolumes):
        values = line.strip().split(" ")[:-2]  # remove priority, volume
        for val_idx, val in enumerate(values):
            values[val_idx] = pad_string(values[val_idx], 4)
        rowIDs["-".join(values)] = idx
    return rowIDs
rowIDs = getRowIDs()


def lcpStateSummary(landscapeFileName, rowIDs=rowIDs):
    """
    Give the summary variables used for stitching based on the landscapes.
    Landscapes are 940X1127X10=10593800 shorts (11653180)
    :param landscapeFileName: The name of the landscape we want to generate a state summary for.
    :return: array of values for distance metric variables

    Fuel Model
    Canopy Closure
    Canopy Height start
    Canopy Base Height start
    Canopy Bulk Density
    Covertype
    Stand Density Index
    Succession Class
    Maximum Time in State
    Stand Volume Age
    highFuel
    modFuel
    lowFuel
    percentHighFuel

    1
    2
    3
    4
    5
    6
    7
    8
    ...
    165
    """

    def getRowID(cover_type, sdi, succession_class, max_time_in_state):
        """
        Get the row's hash key so we can maintain its counter.
        """
        row_hash_key = "{}-{}-{}-{}".format(pad_string(str(cover_type)),
                                         pad_string(str(sdi)),
                                         pad_string(str(succession_class)),
                                         pad_string(str(max_time_in_state)))
        return row_hash_key
    lcpFile = bz2.BZ2File(landscapeFileName, "rb")
    print "processing %s" % lcpFile

    a = array.array('h')
    a.fromstring(lcpFile.read())
    lcpFile.close()
    highFuel = 0
    modFuel = 0
    lowFuel = 0
    summary = []

    layers = {
        "Fuel Model": [],
        "Canopy Closure": [],
        "Canopy Height start": [],
        "Canopy Base Height start": [],
        "Canopy Bulk Density": [],
        "Covertype": [],
        "Stand Density Index": [],
        "Succession Class": [],
        "Maximum Time in State": [],
        "Stand Volume Age": []
    }

    for layerIdx in range(0,11):
        average = 0
        for pixelIdx in range(0,len(a)/11):
            pixel = a[pixelIdx*11 + layerIdx]
            if layerIdx == 0:
                if pixel == 122 or pixel == 145:
                    highFuel += 1
                elif pixel == 121 or pixel == 186:
                    modFuel += 1
                elif pixel == 142 or pixel == 161 or pixel == 187 or pixel == 184 or pixel == 185:
                    lowFuel += 1
            average = float(average * pixelIdx + pixel)/(pixelIdx + 1.)

            if layerIdx == 0:
                layers["Fuel Model"].append(pixel)
            elif layerIdx == 1:
                layers["Canopy Closure"].append(pixel)
            elif layerIdx == 2:
                layers["Canopy Height start"].append(pixel)
            elif layerIdx == 3:
                layers["Canopy Base Height start"].append(pixel)
            elif layerIdx == 4:
                layers["Canopy Bulk Density"].append(pixel)
            elif layerIdx == 5:
                layers["Covertype"].append(pixel)
            elif layerIdx == 6:
                layers["Stand Density Index"].append(pixel)
            elif layerIdx == 7:
                layers["Succession Class"].append(pixel)
            elif layerIdx == 8:
                layers["Maximum Time in State"].append(pixel)
            elif layerIdx == 9:
                layers["Stand Volume Age"].append(pixel)
        summary.append(average)
    del summary[-1] # remove the last element because it is not needed
    summary.append(highFuel)
    summary.append(modFuel)
    summary.append(lowFuel)
    summary.append(float(highFuel)/(highFuel+modFuel+lowFuel))

    counts = [0] * (len(rowIDs.keys()) + 1)  # Add 1 to accomodate duplicate row
    for idx, pixel in enumerate(layers["Fuel Model"]):

        mtis = layers["Maximum Time in State"][idx]

        # The non-growing portions of the landscape are not counted
        if layers["Covertype"][idx] == 99 or layers["Stand Density Index"][idx] == 0 or layers["Covertype"][idx] == 9:
            continue

        # The young pixels are not harvested
        if layers["Maximum Time in State"][idx] < 20:
            continue

        # Lodgepole is not harvested before 80 years
        if layers["Covertype"][idx] == 46 and mtis < 80:
            continue

        # This combination is not harvested
        if layers["Covertype"][idx] == 46 and layers["Stand Density Index"][idx] == 1 and layers["Succession Class"][idx] == 1:
            continue

        # change mtis to 70 when it has values matching the missing values in the table
        if (layers["Covertype"][idx] == 45 or layers["Covertype"][idx] == 43) \
                and layers["Stand Density Index"][idx] == 1 \
                and layers["Succession Class"][idx] == 2 \
                and mtis >= 80 and mtis < 90:
            mtis = 70

        # Round age down to the nearest decade
        rounded = int(mtis / 10)*10
        rounded = min(100, rounded)

        row_hash_key = getRowID(layers["Covertype"][idx],
                         layers["Stand Density Index"][idx],
                         layers["Succession Class"][idx],
                         rounded)
        rowID = rowIDs[row_hash_key]
        counts[rowID] += 1
    for count in counts:
        summary.append(count)
    return summary


def test_post_process_landscapes():
    """
    Generate pickled version of all the state summaries for each of the landscapes in the landscapes directory
    """
    landscape_directory = "/nfs/eecs-fserv/share/rhoutman/FireWoman/results/landscapes/"
    results_directory = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries/"

    #landscape_directory = "/nfs/eecs-fserv/share/rhoutman/FireWoman/results/landscapes_split/"
    #results_directory = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_split/"

    #landscape_directory = "/nfs/eecs-fserv/share/rhoutman/FireWoman/results/landscapes_fuel/"
    #results_directory = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_fuel/"

    #landscape_directory = "/nfs/eecs-fserv/share/mcgregse/starting_landscape_summary_tmp/"
    #results_directory = "/nfs/eecs-fserv/share/mcgregse/starting_landscape_summary/"
    
    all_files = os.listdir(landscape_directory)
    currently_output_files = os.listdir(results_directory)
    files = []
    jump_ahead_count = 500  # Up to how far to jump ahead if a summary was already built

    def diff(first, second):
        second = set(second)
        return [item for item in first if item not in second]

    missing = diff(all_files, currently_output_files)
    for filename in missing:
        if ".lcp.bz2" in filename:
            files.append(filename)

    print "processing {} files".format(len(files))
    file_number = 0

    files.sort()
    while file_number < len(files):
        f = files[file_number]

        print "processing {}".format(f)
        if os.path.isfile(results_directory+f):
            print "skipping forward since this landscape is processed"
            file_number += int(jump_ahead_count * random.random())
            continue
        try:
            s = lcpStateSummary(landscape_directory+f)
            if os.path.isfile(results_directory+f):
                print "skipping forward since this landscape is processed"
                file_number += int(jump_ahead_count * random.random())
                continue
            out = open(results_directory+f, "wb")
            pickle.dump(s, out)
            out.close()
        except Exception as inst:
            print type(inst)
            print inst.args
            print "failed to summarize: {}".format(f)
        file_number += 1


def test_check_for_incomplete_pickles():
    """
    Open all the landscape pickles and check that they are properly formatted. Print the pickles that are not well formatted.
    """
    results_directories = ["/nfs/eecs-fserv/share/mcgregse/landscape_summaries/",
                           "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_fuel/",
                           "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_split/"]
    for resultsDirectory in results_directories:
        files = os.listdir(resultsDirectory)
        file_number = 0
        while file_number < len(files):
            f = open(resultsDirectory + files[file_number], "rb")
            try:
                arr = pickle.load(f)
                assert arr[0] >= 0
                assert arr[1] >= 0
                assert arr[2] >= 0
                assert len(arr) == 187
            except Exception as _:
                print files[file_number]
                print len(arr)
            f.close()
            file_number += 1


def fix_databases(database_input_path, database_output_path):
    """
    The old database generator improperly determined the off-policy Markov state by looking back two rows instead
    of just one. This function fixed the incorrect database. Since I fixed the databases
    and the database processing script, this function is now deprecated.
    :param database_input_path:
    :param database_output_path:
    :return:
    """
    # Each of these variables need a "start" value and an "end" value pulled from the subsequent state
    landscape_summary_names = [
        "Fuel Model",  # \/ pulled from the landscape summary of the prior time step's onPolicy landscape
        "Canopy Closure",
        "Canopy Height",
        "Canopy Base Height",
        "Canopy Bulk Density",
        "Covertype",
        "Stand Density Index",
        "Succession Class",
        "Maximum Time in State",
        "Stand Volume Age",
        "highFuel",
        "modFuel",
        "lowFuel",
        "percentHighFuel"
    ]
    out = file(database_output_path, "w")
    with open(database_input_path, 'rb') as csvfile:
        transitions_reader = csv.DictReader(csvfile)
        transitions = list(transitions_reader)
        for header in transitions_reader.fieldnames:
            out.write(header + ",")
        out.write("\n")
        for idx, transitionDictionary in enumerate(transitions):
            on_policy = int(float(transitionDictionary["onPolicy"])) == 1
            year = transitionDictionary["year"]
            for header in transitions_reader.fieldnames:
                if int(float(year)) == 0:
                    out.write(transitionDictionary[header] + ",")
                else:
                    if not on_policy:
                        true_value = False
                        for fix in landscape_summary_names:
                            if fix + " start" == header:
                                true_value = transitions[idx-1][fix + " end"]
                        if type(true_value) == bool:
                            out.write(transitionDictionary[header] + ",")
                        else:
                            out.write(true_value + ",")
                    else:
                        out.write(transitionDictionary[header] + ",")
            out.write("\n")


def process_database(database_input_path, database_output_path, landscape_summary_path):

    initial_landscape_description = [
        130.011288678,
        27.4871670222,
        475.19681323,
        29.6549113633,
        5.17117748117,
        57.4973352338,
        24.5366554022,
        25.8858577659,
        263.886173989,
        263.886173989,
        138226,
        18429,
        643003,
        0.1728563961,

        # \/ Priority rows
        0, 0, 0, 0, 0, 3384, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48087, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1161, 0, 0, 0, 0, 0, 0, 0, 0, 3019, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 108226, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9068, 0, 0, 105610, 0, 0, 0, 0, 17383, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 70651, 0, 0, 0, 0, 33395, 0, 0, 0, 0, 18429, 0, 0, 0, 0
    ]

    # Each of these variables need a "start" value and an "end" value pulled from the subsequent state
    landscape_summary_names = [
        "Fuel Model",  # \/ pulled from the landscape summary of the prior time step's onPolicy landscape
        "Canopy Closure",
        "Canopy Height",
        "Canopy Base Height",
        "Canopy Bulk Density",
        "Covertype",
        "Stand Density Index",
        "Succession Class",
        "Maximum Time in State",
        "Stand Volume Age",
        "highFuel",
        "modFuel",
        "lowFuel",
        "percentHighFuel"
    ]
    harvest_summary_names = ["PriorityRow" + str(i) for i in range(1, 174)]
    exogenous_summary_names = [
        "Precipitation",  # \/ pulled from the current row's state
        "MaxTemperature",
        "MinHumidity",
        "WindDirection",
        "WindSpeed",
        "ignitionCovertype",
        "ignitionSlope",
        "ignitionLocation",
        "ignitionAspect",
        "ignitionFuelModel",
        "startIndex",
        "ERC",
        "SC"
    ]
    all_stitching_variables_names = landscape_summary_names + harvest_summary_names + exogenous_summary_names

    # These are the variables in the output files as they are ordered in the raw output files.
    # "initialFire, action, year, startIndex, endIndex, ERC, SC, Precipitation, MaxTemperature, MinHumidity, WindDirection, WindSpeed, IgnitionCount, CrownFirePixels, SurfaceFirePixels, fireSuppressionCost, timberLoss_IJWF, lcpFileName, offOnPolicy, ignitionLocation, ignitionCovertype, ignitionAspect, ignitionSlope, ignitionFuelModel, ponderosaSC1, ponderosaSC2, ponderosaSC3, ponderosaSC4, ponderosaSC5, lodgepoleSC1, lodgepoleSC2, lodgepoleSC3, mixedConSC1, mixedConSC2, mixedConSC3, mixedConSC4, mixedConSC5, boardFeetHarvestTotal, boardFeetHarvestPonderosa, boardFeetHarvestLodgepole, boardFeetHarvestMixedConifer"
    raw_header = [
        "initialFire",
        "action",
        "year",
        "startIndex",
        "endIndex",
        "ERC",
        "SC",
        "Precipitation",
        "MaxTemperature",
        "MinHumidity",
        "WindDirection",
        "WindSpeed",
        "IgnitionCount",
        "CrownFirePixels",
        "SurfaceFirePixels",
        "fireSuppressionCost",
        "timberLoss_IJWF",
        "lcpFileName",
        "offPolicy",
        "ignitionLocation",
        "ignitionCovertype",
        "ignitionAspect",
        "ignitionSlope",
        "ignitionFuelModel",
        "ponderosaSC1",
        "ponderosaSC2",
        "ponderosaSC3",
        "ponderosaSC4",
        "ponderosaSC5",
        "lodgepoleSC1",
        "lodgepoleSC2",
        "lodgepoleSC3",
        "mixedConSC1",
        "mixedConSC2",
        "mixedConSC3",
        "mixedConSC4",
        "mixedConSC5",
        "boardFeetHarvestTotal",
        "boardFeetHarvestPonderosa",
        "boardFeetHarvestLodgepole",
        "boardFeetHarvestMixedConifer"
    ]

    out = file(database_output_path, "w")
    for newVar in all_stitching_variables_names:
        out.write(newVar + " start,")
    for newVar in all_stitching_variables_names:
        out.write(newVar + " end,")
    for newVar in raw_header:
        out.write(newVar + ",")
    out.write("\n")

    def get_landscape_summary(path, landscape_summary_path=landscape_summary_path):
        lcp_name = path.split("/")[-1] + ".bz2"
        lcp_path = landscape_summary_path + lcp_name
        if os.path.isfile(lcp_path):
            f = open(lcp_path, "rb")
            lcp_summary = pickle.load(f)
            f.close()
        else:
            print "Landscape not found!"
            print lcp_path
            assert False
        return lcp_summary

    with open(database_input_path, 'rb') as csvfile:
        transitions_reader = csv.DictReader(csvfile, fieldnames=raw_header)
        transitions = list(transitions_reader)
        for idx, transitionDictionary in enumerate(transitions):

            year = int(transitionDictionary["year"])
            on_policy = int(transitionDictionary["onPolicy"])

            # We can't render year 100 because there is no fire experienced at that year
            if year == 99:
                continue

            # Get the current transition's lcp summary, or the initial states if it is year 0
            if year == 0:
                current_lcp_summary = initial_landscape_description
            else:
                if on_policy:
                    current_lcp_summary = get_landscape_summary(transitions[idx - 2]["lcpFileName"])
                else:
                    current_lcp_summary = get_landscape_summary(transitions[idx - 1]["lcpFileName"])

            # Write the lcp's summary to the "start" portion
            for entry in current_lcp_summary:
                out.write(str(entry) + ",")

            # Write the "other" starting features
            for name in exogenous_summary_names:
                out.write(str(transitionDictionary[name]) + ",")

            # Write the lcp's summary from transitions[idx]
            current_lcp_summary = get_landscape_summary(transitionDictionary["lcpFileName"])
            for entry in current_lcp_summary:
                out.write(str(entry) + ",")

            # Write the "other" ending features from transitions[idx + 2]
            for name in exogenous_summary_names:
                out.write(str(transitions[idx+2][name]) + ",")

            # Write out the rest of the result file. Yes there will be duplicates
            for k in raw_header:
                cur = transitionDictionary[k]
                if cur is None:
                    cur = ""
                else:
                    cur = str(cur)
                out.write(cur + ",")
            out.write("\n")

def test_process_raw_output():
    """
    Process all the raw output files into their own files without the surrounding whitespace
    """
    # Fuel policy
    # estimatedpolicy-HIGH_FUEL_POLICY-i-[3-6][0-9].out
    # Location policy
    # estimatedpolicy-IGNITION_POLICY-i-*-erc-65-days-100.out
    # Severity policy
    # estimatedpolicy-SPLIT_LANDSCAPE_POLICY-i-[0-3][0-9].out
    # database policy
    # estimatedpolicy-IGNITION_POLICY-i-1-erc-*-days-*.out
    """
    pre-processing steps

    grep CSVROWFORPARSER estimatedpolicy-HIGH_FUEL_POLICY-i-[3-6][0-9].out -h | sed 's/^.................//' > ../databases/fuel_raw_policy.csv

    grep CSVROWFORPARSER estimatedpolicy-SPLIT_LANDSCAPE_POLICY-i-[0-3][0-9].out -h | sed 's/^.................//' > ../databases/location_raw_policy.csv

    grep CSVROWFORPARSER estimatedpolicy-IGNITION_POLICY-i-*-erc-65-days-100.out -h | sed 's/^.................//' > ../databases/intensity_raw_policy.csv

    grep CSVROWFORPARSER estimatedpolicy-IGNITION_POLICY-i-1-erc-*-days-*.out -h | sed 's/^.................//' > ../databases/raw_database.csv
    """
    databases = [
        ["../databases/fuel_raw_policy.csv",
         "../databases/fuel_policy.csv",
         "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_fuel/"],
        ["../databases/location_raw_policy.csv",
         "../databases/location_policy.csv",
         "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_split/"],
        ["../databases/intensity_raw_policy.csv",
         "../databases/intensity_policy.csv",
         "/nfs/eecs-fserv/share/mcgregse/landscape_summaries/"],
        ["../databases/raw_database.csv",
         "../databases/database.csv",
         "/nfs/eecs-fserv/share/mcgregse/landscape_summaries/"]
    ]
    for d in databases:
        print "processing {}".format(d)
        process_database(d[0], d[1], d[2])
