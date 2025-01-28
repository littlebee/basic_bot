#!/bin/sh

# this script is use to build basic_bot itself.  Not included in
# the files that `bb_create` creates.

rm -Rf src/basic_bot/created_files/webapp/node_modules
rm -Rf src/basic_bot/created_files/webapp/package-lock.json

# fail on any error
set -e

echo "Linting..."
python3 -m flake8 src/basic_bot

echo "Running mypy \(typechecker\): $(python3 -m mypy --version)"
python3 -m mypy src/basic_bot

echo "Building package"
python3 -m build
