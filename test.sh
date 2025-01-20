#!/bin/sh

echo "\n Running integration tests...\n"
pytest tests/

echo "\n Running e2e tests.  This may take a few minutes...\n"
pytest tests_e2e/

