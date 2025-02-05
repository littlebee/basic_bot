#!/bin/bash

# fail on any error
set -e

python -m pip install -r requirements.txt

./build.sh
python -m pip install --editable .
