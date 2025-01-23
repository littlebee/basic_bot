#!/bin/sh

set -e

echo "\n Running integration tests...\n"
pytest tests/integration_tests/

echo "\n Running e2e tests.  This may take a few minutes...\n"
pytest tests/e2e_tests/

# field tests are not run on the target machine where we can install
# platform specific dependencies
# echo "\n Running field tests...\n"
# pytest tests/field_tests/

