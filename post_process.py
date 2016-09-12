import os
from subprocess import call
from struct import unpack
import pickle
import nose.tools

def lcpStateSummary(landscapeFileName):
    """
    Give the summary variables used for stitching based on the landscapes.
    Landscapes are 940X1127X10=10593800 shorts (11653180)
    :param landscapeFileName: The name of the landscape we want to generate a state summary for.
    :return: array of values for distance metric variables
    """
    distanceMetricVariableCount = 10

    # tmpFileName
    decompressedFilename = "/nfs/eecs-fserv/share/mcgregse/tmp/tmp.lcp." + landscapeFileName.split("/")[-1]

    call(["bzip2 " + landscapeFileName + " -dkc > " + decompressedFilename], shell=True)

    lcpFile = file(decompressedFilename, "rb")
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
    summary = []
    for layerIdx, layer in enumerate(layers):
        average = 0
        for idx, pixel in enumerate(layers[layerIdx]):
            average = float(average * idx + pixel)/(idx + 1.)
        summary.append(average)
    print "removing file {}".format(decompressedFilename)
    call(["rm " + decompressedFilename], shell=True) # cleanup decompressed file
    del summary[-1] # remove the last element because it is not needed
    return summary

def test_post_process_landscapes():
    """
    Generate pickled version of all the state summaries for each of the landscapes in the landscapes directory
    """
    landscapeDirectory = "/nfs/eecs-fserv/share/rhoutman/FireWoman/results/landscapes"
    resultsDirectory = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries"
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
    fileNum = len(files)-1
    while fileNum >= 0:
        f = files[fileNum]

        print "processing {}".format(f)
        if os.path.isfile(resultsDirectory+f):
            print "skipping forward {} since this landscape is processed".format(10)
            fileNum += 10
            continue
        try:
            s = lcpStateSummary(landscapeDirectory+f)
            if os.path.isfile(resultsDirectory+f):
                print "skipping forward {} since this landscape is processed".format(10)
                fileNum += 10
                continue
            out = open(resultsDirectory+f, "wb")
            pickle.dump(s, out)
            out.close()
        except Exception as inst:
            print type(inst)
            print inst.args
            print "failed to summarize: {}".format(f)
        fileNum += (-1)


def test_check_for_incomplete_pickles():
    """
    Open all the landscape pickles and check that they are properly formatted. Print the pickles that are not well formatted.
    """
    resultsDirectory = "/nfs/eecs-fserv/share/mcgregse/landscape_summaries"
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
