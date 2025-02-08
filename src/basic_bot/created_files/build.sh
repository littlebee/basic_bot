#!/bin/sh

if [ "$(which npm)"=="" ]; then
    echo "\n******************* ERROR *******************"
    echo "Unable to build the webapp because npm not found.\nPlease install nodejs."
    echo "*********************************************\n\n"
    exit 1
fi


# echo on
set -x
# stop on error
set -e

# TODO : maybe add flake8 tests and black formatting
#   the real question there is do I make those dependencies
#   of the basic_bot pip.  I want to be agnostic to the
#   use preferred python linter and formatter.


cd webapp
npm install
npm run build

