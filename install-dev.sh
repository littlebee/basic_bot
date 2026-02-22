#!/bin/bash

# fail on any error
set -e

# if running on the CI server, we want to install the dependencies from requirements_CI.txt instead of requirements.txt
if [ "$CI" = "true" ]; then
    echo "Running on CI server, installing dependencies from requirements_CI.txt"
    python -m pip install -r requirements_CI.txt
else
    echo "Running locally, installing dependencies from requirements.txt"
    python -m pip install -r requirements.txt
fi

./build.sh
python -m pip install --editable .
