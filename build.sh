#!/bin/sh

# this script is use to build basic_bot itself.  Not included in
# the files that `bb_create` creates.

rm -Rf src/basic_bot/created_files/webapp/node_modules
rm -Rf src/basic_bot/created_files/webapp/package-lock.json

# fail on any error
set -e

echo "Linting..."
python -m flake8 src/basic_bot

echo "Running mypy (typechecker): $(python -m mypy --version)"
python -m mypy src/basic_bot

echo "Building pip package"
python -m build
