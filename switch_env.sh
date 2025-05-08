#!/bin/bash

# This is a commented-out Bash script (switch_env.sh) for the LSU Datastore Dashboard.
# It provides a utility to switch between different Conda environments (dev-env, prod-env, test-env, airflow-env)
# defined in the project's YAML files, allowing team members to easily manage development, testing, production, and
# workflow orchestration setups for the Team-34 project. While not currently used, this script could be leveraged in
# the future to:
# - Streamline environment switching for developers working on different aspects of the project (e.g., running the
#   Streamlit app with dev-env, testing with test-env, or deploying with prod-env).
# - Support local testing and development workflows by ensuring the correct environment is activated before running
#   scripts like app.py, fetch_lsu_course_data, or pytest tests (test_connector.py, test_processor.py).
# - Facilitate production deployment by activating prod-env before launching a FastAPI/Flask API or Streamlit app with
#   gunicorn/uvicorn (as defined in prod-env.yml).
# - Enable Airflow-based workflow orchestration by activating airflow-env before running DAGs (e.g., automating
#   fetch_lsu_course_data or parse_course_page tasks).
# To use this script, ensure the Conda environments are created (e.g., `conda env create -f dev-env.yml`), then run:
# `sh switch_env.sh dev` (or prod, test, airflow). The script keeps the shell active in the selected environment.

## Ensure Conda is initialized
#if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
#    source "$HOME/anaconda3/etc/profile.d/conda.sh"
#else
#    echo "Error: Conda initialization script not found!"
#    exit 1
#fi
#
## Select environment
#if [ "$1" == "dev" ]; then
#    conda activate dev-env
#    echo "Switched to Development Environment (dev-env)"
#elif [ "$1" == "prod" ]; then
#    conda activate prod-env
#    echo "Switched to Production Environment (prod-env)"
#elif [ "$1" == "test" ]; then
#    conda activate test-env
#    echo "Switched to Testing Environment (test-env)"
#elif [ "$1" == "airflow" ]; then
#    conda activate airflow-env
#    echo "Switched to Airflow Environment (airflow-env)"
#else
#    echo "Usage: sh switch_env.sh [dev|prod|test|airflow]"
#    exit 1
#fi
#
## Keep the shell active in the new environment
#$SHELL
