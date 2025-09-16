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

echo "Building pip package"
python -m build
