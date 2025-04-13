#!/bin/bash

# Ensure Conda is initialized
if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    echo "Error: Conda initialization script not found!"
    exit 1
fi

# Select environment
if [ "$1" == "dev" ]; then
    conda activate dev-env
    echo "Switched to Development Environment (dev-env)"
elif [ "$1" == "prod" ]; then
    conda activate prod-env
    echo "Switched to Production Environment (prod-env)"
elif [ "$1" == "test" ]; then
    conda activate test-env
    echo "Switched to Testing Environment (test-env)"
elif [ "$1" == "airflow" ]; then
    conda activate airflow-env
    echo "Switched to Airflow Environment (airflow-env)"
else
    echo "Usage: sh switch_env.sh [dev|prod|test|airflow]"
    exit 1
fi

# Keep the shell active in the new environment
$SHELL
