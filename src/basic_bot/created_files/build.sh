#!/bin/sh

# echo on
set -x
# stop on error
set -e

# TODO : maybe add flake8 tests and black formatting
#   the real question there is do I make those dependencies
#   of the basic_bot pip

cd webapp && npm install && npm run build

