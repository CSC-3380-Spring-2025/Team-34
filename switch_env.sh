#!/bin/bash

# Ensure Conda is initialized
source ~/anaconda3/etc/profile.d/conda.sh

# Select environment
if [ "$1" == "dev" ]; then
    exec bash -c "conda activate dev-env && bash"
elif [ "$1" == "prod" ]; then
    exec bash -c "conda activate prod-env && bash"
elif [ "$1" == "test" ]; then
    exec bash -c "conda activate test-env && bash"
else
    echo "Usage: sh switch_env.sh [dev|prod|test]"
fi
