#!/bin/bash
set -e
./build.sh
pip3 install --break-system-packages --editable .
