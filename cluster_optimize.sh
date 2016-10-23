#!/bin/bash

PYTHONPATH="/nfs/guille/tgd/users/mcgregse/anaconda2/bin/python2.7"
uuid=$(uuidgen)

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

if [[ $# -eq 1 ]]; then
    files=("z"$uuid)
else
    echo "Usage: cluster_optimize.sh <test-selector>"
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
    echo $PYTHONPATH "-t $uuid">> $g

    # Wait for the server to start
    echo "while [ ! -f servers/$uuid ]">> $g
    echo 'do'>> $g
    echo  'sleeping for 10'>> $g
    echo  'sleep 10'>> $g
    echo 'done'>> $g

    # Ask for the optimization
    echo "curl http://localhost:8938/optimize?Sample%20Count=30&Horizon=99&Render%20Ground%20Truth=0&Use%20Location%20Policy=0&Use%20Landscape%20Policy=0&ERC%20Threshold=71&Days%20Until%20End%20of%20Season%20Threshold=51&Number%20of%20Runs%20Limit=500">> $g

    qsub $g
    sleep 1
done
