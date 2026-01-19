#!/bin/bash
# Usage: <actions_json_file.json> <config_file.xlsx> <output_results.xlsx>

container_id="water_futures_battle"   # Assume docker image is called "water_futures_battle"

# Note: This script assumes that the docker image is already running -- 
# might be more efficient to keep it running instead of restarting it every time the evaluation is started
#docker run $container_id

# Copy input file to docker
docker cp $1 $container_id:/my_actions.json
docker cp $2 $container_id:/my_config.xlsx

# Run evaluation inside docker
docker exec $container_id water_futures_battle_run_eval actions_json_file=my_actions.json config_file=my_config.xlsx

# Extract results
docker cp $container_id:/results.xlsx $3

# Stop/Quit docker image
#docker stop $container_id