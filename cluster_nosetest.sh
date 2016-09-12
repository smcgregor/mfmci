#!/bin/bash

NOSEPATH="/nfs/guille/tgd/users/mcgregse/anaconda2/bin/nosetests"
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
    echo "Usage: submit.sh <test-selector>"
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
    echo $NOSEPATH "$1 -s">> $g
    # echo 'if ! $?; then sleep 60; exit 100; fi'>> $g
    qsub $g
    sleep 1
done
