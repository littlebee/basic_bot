#!/bin/sh

set -e

echo "\n Running integration tests...\n"
pytest -v tests/integration_tests/

echo "\n Running e2e tests.  This may take a few minutes...\n"
pytest -v tests/e2e_tests/

# field tests are not run on the target machine where we can install
# platform specific dependencies
# echo "\n Running field tests...\n"
# pytest tests/field_tests/

