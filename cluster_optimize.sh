#!/bin/bash

PYTHONPATH="/nfs/guille/tgd/users/mcgregse/anaconda2/bin/python2.7"
uuid=$(uuidgen)
smac_runs_limit="300"
smac_horizon="99"
smac_sample_count="30"

rewards_suppression=$1
rewards_timber=$2
rewards_ecology=$3
rewards_air=$4
rewards_recreation=$5

high_fuel_count_1=10000
high_fuel_count_2=10000
erc_1=90
erc_2=90
erc_3=90
erc_4=90
day_1=120
day_2=120
day_3=120
day_4=120
day_5=120
day_6=120
day_7=120
day_8=120

# ----------------------------------------------------------------------------
# Process the node blacklist

if [ -e "cluster_blacklist.txt" ]; then
    function join { local IFS="$1"; shift; echo "$*"; }

    blacklist_string=$(cat cluster_blacklist.txt | tr "\n" " ")
    blacklist_array=($blacklist_string)
    end=$(( ${#blacklist_array[@]} - 1 ))
    for i in $(seq 0 $end)
    do
	echo "Blacklisting '""${blacklist_array[$i]}""'"
blacklist_array[$i]="!""${blacklist_array[$i]}"
done

blacklist=$(join "&" ${blacklist_array[@]})
fi

# ----------------------------------------------------------------------------
# Construct job scripts

if [[ $# -eq 5 ]]; then
    files=("z"$uuid)
else
    echo "Usage: cluster_optimize.sh {0,1}<Suppression> {0,1}<Timber>  {0,1}<Ecology> {0,1}<Air> {0,1}<Recreation> "
    exit 0
fi

# This restricts the job to run on nodes that are known to have the same
# processor architecture and clock speed
hostnames=""
if [ -n "$blacklist" ]; then
    hostnames="$blacklist"
fi
echo $hostnames

for f in ${files[@]}
do
    echo $f
    g="$f"".sh"
    rm -f $g
    touch $g
    echo '#!/bin/bash'>> $g
    echo '#$ -cwd'>> $g
    echo '#$ -m e'>> $g
    echo '#$ -M smcgregor@seanbmcgregor.com'>> $g
    # echo '#$ -N '"$f">> $g
    echo '#$ -hard -l m_mem_free=8G'>> $g
    echo '#$ -l hostname='"$hostnames">> $g

    # Start the server
    echo $PYTHONPATH "flask_server.py wildfire surrogate $uuid $PYTHONPATH &">> $g

    # Wait for the server to start
    echo "while [ ! -f servers/$uuid ]">> $g
    echo 'do'>> $g
    echo  'echo "sleeping for 10"'>> $g
    echo  'sleep 10'>> $g
    echo 'done'>> $g

    # Ask for the optimization
    #echo 'curl "http://localhost:8938/optimize?Sample%20Count=30&Horizon=99&Render%20Ground%20Truth=0&Use%20Location%20Policy=0&Use%20Landscape%20Policy=0&ERC%20Threshold=71&Days%20Until%20End%20of%20Season%20Threshold=51&Number%20of%20Runs%20Limit=500"'>> $g
    #echo "curl 'http://localhost:8938/optimize?Use%20Tree%20Policy=1&high_fuel_count=0&fire_size_differential_1=0&fire_size_differential_2=0&fire_suppression_cost_1=0&fire_suppression_cost_2=0&fire_suppression_cost_3=0&fire_suppression_cost_4=0&fire_days_differential_1=0&fire_days_differential_2=0&fire_days_differential_3=0&fire_days_differential_4=0&fire_days_differential_5=0&fire_days_differential_6=0&fire_days_differential_7=0&fire_days_differential_8=0&Sample%20Count=$smac_sample_count&Horizon=$smac_horizon&Render%20Ground%20Truth=0&restoration%20index%20dollars=0&ponderosa%20price%20per%20bf=0&mixed%20conifer%20price%20per%20bf=0&lodgepole%20price%20per%20bf=0&airshed%20smoke%20reward%20per%20day=0&recreation%20index%20dollars=0&suppression%20expense%20dollars=1&Use%20Location%20Policy=0&Use%20Landscape%20Policy=0&ERC%20Threshold=65&Days%20Until%20End%20of%20Season%20Threshold=100&Number%20of%20Runs%20Limit=$smac_runs_limit&discount=0.96&rewards_suppression=$rewards_suppression&rewards_timber=$rewards_timber&rewards_ecology=$rewards_ecology&rewards_air=$rewards_air&rewards_recreation=$rewards_recreation'" >> $g
    echo "curl 'http://localhost:8938/optimize?high_fuel_count_1=$high_fuel_count_1&high_fuel_count_2=$high_fuel_count_2&erc_1=$erc_1&erc_2=$erc_2&erc_3=$erc_3&erc_4=$erc_4&day_1=$day_1&day_2=$day_2&day_3=$day_3&day_4=$day_4&day_5=$day_5&day_6=$day_6&day_7=$day_7&day_8=$day_8&Use%20Tree%20Policy=1&high_fuel_count=0&fire_size_differential_1=0&fire_size_differential_2=0&fire_suppression_cost_1=0&fire_suppression_cost_2=0&fire_suppression_cost_3=0&fire_suppression_cost_4=0&fire_days_differential_1=0&fire_days_differential_2=0&fire_days_differential_3=0&fire_days_differential_4=0&fire_days_differential_5=0&fire_days_differential_6=0&fire_days_differential_7=0&fire_days_differential_8=0&Sample%20Count=$smac_sample_count&Horizon=$smac_horizon&Render%20Ground%20Truth=0&restoration%20index%20dollars=0&ponderosa%20price%20per%20bf=0&mixed%20conifer%20price%20per%20bf=0&lodgepole%20price%20per%20bf=0&airshed%20smoke%20reward%20per%20day=0&recreation%20index%20dollars=0&suppression%20expense%20dollars=1&Use%20Location%20Policy=0&Use%20Landscape%20Policy=0&ERC%20Threshold=65&Days%20Until%20End%20of%20Season%20Threshold=100&Number%20of%20Runs%20Limit=$smac_runs_limit&discount=0.96&rewards_suppression=$rewards_suppression&rewards_timber=$rewards_timber&rewards_ecology=$rewards_ecology&rewards_air=$rewards_air&rewards_recreation=$rewards_recreation'" >> $g
    #high_fuel_count_1=$high_fuel_count_1&high_fuel_count_2=$high_fuel_count_2&erc_1=$erc_1&erc_2=$erc_2&erc_3=$erc_3&erc_4=$erc_4&day_1=$day_1&day_2=$day_2&day_3=$day_3&day_4=$day_4&day_5=$day_5&day_6=$day_6&day_7=$day_7&day_8=$day_8&

    qsub $g
    sleep 1
done
