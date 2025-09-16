#!/bin/sh

# fail on any error
set -e

echo "Linting with flake8..."
python -m flake8 src/basic_bot

echo "Running mypy (typechecker): $(python -m mypy --version)"
python -m mypy src/basic_bot

