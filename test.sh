#!/bin/sh

set -e

echo "\n Running unit tests...\n"
python -m pytest -vv tests/unit_tests/

echo "\n Running integration tests...\n"
python -m pytest -vv tests/integration_tests/

echo "\n Running e2e tests.  This may take a few minutes...\n"
python -m pytest -vv tests/e2e_tests/

# Field tests are typically run on the target machine where we can install
# platform specific dependencies
# echo "\n Running field tests...\n"
# pytest tests/field_tests/

