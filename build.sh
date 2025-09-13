#!/bin/sh

# this script is use to build basic_bot itself.  Not included in
# the files that `bb_create` creates.


# this can fail on linux or if running on a machine without a node
# installed
echo "Installing npm dependencies locally..."
cd src/basic_bot/created_files/webapp/ && npm install
cd ../../../..

# fail on any error
set -e

echo "Linting..."
python -m flake8 src/basic_bot

echo "Running mypy (typechecker): $(python -m mypy --version)"
echo "Using strict type checking configuration (.mypy.ini)"
python -m mypy --no-incremental --show-error-codes src/basic_bot

echo "Building pip package"
python -m build
