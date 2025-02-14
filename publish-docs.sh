#!/bin/sh

set -x  # echo on
set -e  # stop on error

python ./build-docs.py
mkdocs gh-deploy
