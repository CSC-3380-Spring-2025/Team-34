#!/bin/bash

if [ "$1" == "dev" ]; then
    conda activate dev-env
    echo "Switched to Development Environment (dev-env)"
elif [ "$1" == "prod" ]; then
    conda activate prod-env
    echo "Switched to Production Environment (prod-env)"
elif [ "$1" == "test" ]; then
    conda activate test-env
    echo "Switched to Testing Environment (test-env)"
else
    echo "Usage: ./switch_env.sh [dev|prod|test]"
fi
