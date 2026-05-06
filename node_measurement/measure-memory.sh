#!/bin/bash

DURATION=30  # 30 seconds per test
BUFFER=15
## HU RAPL PATH
RAPL_PATH="/sys/class/powercap/intel-rapl:0/intel-rapl:0:0/energy_uj"  # HU NODE
## GPG RAPL PATHS
# RAPL_PATH_0="/sys/class/powercap/intel-rapl:0/intel-rapl:0:1/energy_uj"  # GPG NODE
# RAPL_PATH_1="/sys/class/powercap/intel-rapl:1/intel-rapl:1:1/energy_uj"  # GPG NODE
TOTAL_RAM=$1
OUT_PATH="memory.csv"

# setup output file
echo "load,ram,watts,val" > $OUT_PATH

for load in $(seq 0 10 100); do
	request=$((TOTAL_RAM * load / 100))
	echo "load ${load}% (${request} GB)"

	if [ $load -gt 0 ]; then
		stress-ng --vm 1 --vm-bytes ${request}g --vm-keep -t $((DURATION + BUFFER)) & STRESS_PID=$!
		sleep $BUFFER
	fi

	start=$(cat $RAPL_PATH)
    # start=$(($(sudo cat $RAPL_PATH_0) + $(sudo cat $RAPL_PATH_1)))  ## GPG NODE
	sleep $DURATION
    end=$(cat $RAPL_PATH)
    # end=$(($(sudo cat $RAPL_PATH_0) + $(sudo cat $RAPL_PATH_1)))  ## GPG NODE

	watts=$(awk "BEGIN { print (($end - $start) * 1e-6) / $DURATION }")
	w_per_gb=$(awk "BEGIN { print $watts / $TOTAL_RAM }")

	echo "${watts} W -> ${w_per_gb} W/GB"
	echo "$load,$request,$watts,$w_per_gb" >> $OUT_PATH

	[ $load -gt 0 ] && wait $STRESS_PID
	sleep 5
done
