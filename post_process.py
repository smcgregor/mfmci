import os
from subprocess import call
from struct import unpack
import pickle
import nose.tools
import bz2
import random

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

    lcpFile = bz2.BZ2File(landscapeFileName, "r")
    print "processing %s" % lcpFile
    layers = []
    for idx in range(0,distanceMetricVariableCount):
        layers.append([])
    layers.append([]) # hack because there is an extra layer

    shortCount = 0 # 0 to 10,593,800
    shortBytes = lcpFile.read(2)
    while shortBytes != "":
        pix = unpack("<h", shortBytes)
        layers[shortCount % len(layers)].append(pix[0])
        shortCount += 1
        shortBytes = lcpFile.read(2)
    lcpFile.close()
    highFuel = 0
    modFuel = 0
    lowFuel = 0
    summary = []
    for layerIdx, layer in enumerate(layers):
        average = 0
        for idx, pixel in enumerate(layers[layerIdx]):
            if layerIdx == 0:
                if pixel == 122 or pixel == 145:
                    highFuel += 1
                elif pixel == 121 or pixel == 186:
                    modFuel += 1
                elif pixel == 142 or pixel == 161 or pixel == 187 or pixel == 184 or pixel == 185:
                    lowFuel += 1
            average = float(average * idx + pixel)/(idx + 1.)
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
    fileNum = int(100*random.random())
    #fileNum = 0
    while fileNum < len(files):
        f = files[fileNum]

        print "processing {}".format(f)
        if os.path.isfile(resultsDirectory+f):
            print "skipping forward since this landscape is processed"
            fileNum += int(200*random.random())
            continue
        try:
            s = lcpStateSummary(landscapeDirectory+f)
            if os.path.isfile(resultsDirectory+f):
                print "skipping forward since this landscape is processed"
                fileNum += int(200*random.random())
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
    resultsDirectory = "/scratch/mcgregse/aaai/landscape_summaries/"
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
