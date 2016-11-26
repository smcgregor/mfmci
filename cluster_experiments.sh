#!/usr/bin/env bash

# Script for running optimization paper experiments on the cluster #
# The MFMCi experiments can be found in the experiments.py script #

# Run optimization Experiments for different reward functions.
# Each of these script invocations start a cluster node
# that will start the MFMCi flask server, then call the
# "optimize" endpoint of the flask server by
# curling it.

## Composite Objective (Suppression, Timber, Ecology, Air, Recreation)
./cluster_optimize.sh 1 1 1 1 1

## Politics Objective (Timber, Ecology, Air, Recreation)
./cluster_optimize.sh 0 1 1 1 1

## Home Owners Objective (Air, Recreation)
./cluster_optimize.sh 0 0 0 1 1

## Timber Objective (Suppression, Timber)
./cluster_optimize.sh 1 1 0 0 0

# todo

## GP library?

## gradient methods?

## different heuristic?

