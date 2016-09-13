import os
from subprocess import call
from struct import unpack
import pickle
import nose.tools
import bz2
import random
import re
import csv
import array

def lcpStateSummary(landscapeFileName):
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
    """
    distanceMetricVariableCount = 10

    lcpFile = bz2.BZ2File(landscapeFileName, "rb")
    print "processing %s" % lcpFile

    a = array.array('h')
    a.fromstring(lcpFile.read())
    lcpFile.close()
    highFuel = 0
    modFuel = 0
    lowFuel = 0
    summary = []
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
        summary.append(average)
    del summary[-1] # remove the last element because it is not needed                                                                                                                                                                    
    summary.append(highFuel)
    summary.append(modFuel)
    summary.append(lowFuel)
    summary.append(float(highFuel)/(highFuel+modFuel+lowFuel))
    return summary

def test_post_process_landscapes():
    """
    Generate pickled version of all the state summaries for each of the landscapes in the landscapes directory
    """
    landscapeDirectory = "/nfs/eecs-fserv/share/rhoutman/FireWoman/results/landscapes/"
    resultsDirectory = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries/"
    allFiles = os.listdir(landscapeDirectory)
    currentlyOutputFiles = os.listdir(resultsDirectory)
    files = []

    def diff(first, second):
        second = set(second)
        return [item for item in first if item not in second]

    missing = diff(allFiles, currentlyOutputFiles)
    for filename in missing:
        if ".lcp.bz2" in filename:
            files.append(filename)

    print "processing {} files".format(len(files))
    fileNum = int(len(files)*random.random())
    #fileNum = 0

    files.sort()
    while fileNum < len(files):
        f = files[fileNum]

        print "processing {}".format(f)
        if os.path.isfile(resultsDirectory+f):
            print "skipping forward since this landscape is processed"
            fileNum += int(500*random.random())
            continue
        try:
            s = lcpStateSummary(landscapeDirectory+f)
            if os.path.isfile(resultsDirectory+f):
                print "skipping forward since this landscape is processed"
                fileNum += int(500*random.random())
                continue
            out = open(resultsDirectory+f, "wb")
            pickle.dump(s, out)
            out.close()
        except Exception as inst:
            print type(inst)
            print inst.args
            print "failed to summarize: {}".format(f)
        fileNum += 1


def test_check_for_incomplete_pickles():
    """
    Open all the landscape pickles and check that they are properly formatted. Print the pickles that are not well formatted.
    """
    resultsDirectories = ["/nfs/eecs-fserv/share/mcgregse/landscape_summaries/",
                          "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_fuel/",
                          "/nfs/eecs-fserv/share/mcgregse/landscape_summaries_split/"]
    for resultsDirectory in resultsDirectories:
        files = os.listdir(resultsDirectory)
        fileNum = 0
        while fileNum < len(files):
            f = open(resultsDirectory + files[fileNum],"rb")
            try:
                arr = pickle.load(f)
                assert arr[0] >= 0
                assert arr[1] >= 0
                assert arr[2] >= 0
            except Exception as inst:
                print files[fileNum]
            f.close()
            fileNum += 1

def process_database(database_input_path, database_output_path):

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
        0.1728563961
    ]

    # Each of these variables need a "start" value and an "end" value pulled from the subsequent state
    ALL_STITCHING_VARIABLES_NAMES = [
        "Fuel Model", # \/ pulled from the landscape summary of the prior time step's onPolicy landscape
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
        "percentHighFuel",
        "Precipitation", # \/ pulled from the current row's state
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

    # todo: this header does not appear to be correct
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
    for newVar in ALL_STITCHING_VARIABLES_NAMES:
        out.write(newVar + " start,")
    for newVar in ALL_STITCHING_VARIABLES_NAMES:
        out.write(newVar + " end,")
    for newVar in raw_header:
        out.write(newVar + ",")
    out.write("\n")

    def get_landscape_summary(path):
        lcp_name = path.split("/")[-1] + ".bz2"
        lcp_path = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries/" + lcp_name

        if lcp_name == "lcp_1_1_1_50_100_offPolicy.lcp.bz2" or lcp_name == "lcp_1_1_1_70_60_offPolicy.lcp.bz2":
            return initial_landscape_description # todo, remove this trajectory set

        if os.path.isfile(lcp_path):
            f = open(lcp_path, "rb")
            current_lcp_summary = pickle.load(f)
            f.close()
        else:
            print "Landscape not found!"
            print lcp_path
            assert False
            return initial_landscape_description # todo: remove this, this is only here for testing the pipeline
        return current_lcp_summary

    with open(database_input_path, 'rb') as csvfile:
        transitionsReader = csv.DictReader(csvfile, fieldnames=raw_header)
        transitions = list(transitionsReader)
        for idx, transitionDictionary in enumerate(transitions):

            year = int(transitionDictionary["year"])

            # We can't render year 100 because there is no fire experienced at that year
            if year == 99:
                continue

            # Get the current transition's lcp summary, or the initial states if it is year 0
            if year == 0:
                current_lcp_summary = initial_landscape_description
            else:
                current_lcp_summary = get_landscape_summary(transitions[idx - 2]["lcpFileName"])

            # Write the lcp's summary to the "start" portion
            for entry in current_lcp_summary:
                out.write(str(entry) + ",")

            # Write the "other" starting features
            for name in ALL_STITCHING_VARIABLES_NAMES[14:]:
                out.write(str(transitionDictionary[name]) + ",")

            # Write the lcp's summary from transitions[idx]
            current_lcp_summary = get_landscape_summary(transitionDictionary["lcpFileName"])
            for entry in current_lcp_summary:
                out.write(str(entry) + ",")

            # Write the "other" ending features from transitions[idx + 2]
            for name in ALL_STITCHING_VARIABLES_NAMES[14:]:
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
    # estimatedpolicy-IGNITION_POLICY-i-[0-3][0-9]-erc-75-days-120.out
    # Severity policy
    # estimatedpolicy-SPLIT_LANDSCAPE_POLICY-i-[0-3][0-9].out
    # database policy
    # estimatedpolicy-IGNITION_POLICY-i-1-erc-*-days-*.out
    """
    pre-processing steps

    grep CSVROWFORPARSER estimatedpolicy-HIGH_FUEL_POLICY-i-[3-6][0-9].out -h | sed 's/^.................//' > ../databases/fuel_raw_policy.csv

    grep CSVROWFORPARSER estimatedpolicy-SPLIT_LANDSCAPE_POLICY-i-[0-3][0-9].out -h | sed 's/^.................//' > ../databases/location_raw_policy.csv

    grep CSVROWFORPARSER estimatedpolicy-IGNITION_POLICY-i-[0-3][0-9]-erc-75-days-120.out -h | sed 's/^.................//' > ../databases/intensity_raw_policy.csv

    grep CSVROWFORPARSER estimatedpolicy-IGNITION_POLICY-i-1-erc-*-days-*.out -h | sed 's/^.................//' > ../databases/raw_database.csv
    """
    databases = [
        ["../databases/fuel_raw_policy.csv", "../databases/fuel_policy.csv"],
        ["../databases/location_raw_policy.csv", "../databases/location_policy.csv"],
        ["../databases/intensity_raw_policy.csv", "../databases/intensity_policy.csv"],
        ["../databases/raw_database.csv", "../databases/database.csv"]
    ]
    for d in databases:
        print "processing {}".format(d)
        process_database(d[0], d[1])
