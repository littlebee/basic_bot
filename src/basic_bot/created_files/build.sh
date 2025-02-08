#!/bin/sh

# if [ "$(which npm)"=="" ]; then
#     echo "\n******************* ERROR *******************"
#     echo "Unable to build the webapp because npm not found.\nPlease install nodejs."
#     echo "*********************************************\n\n"
#     exit 1
# fi


# echo on
set -x
# stop on error
set -e

# TODO : maybe add flake8 tests and black formatting.
#   basic_bot wants to be agnostic to the user preferred python
#   linter, formatter, type checker etc.


cd webapp
npm install
npm run build

