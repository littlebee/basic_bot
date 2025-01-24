#!/bin/sh

rm -Rf src/basic_bot/created_files/webapp/node_modules
rm -Rf src/basic_bot/created_files/webapp/package-lock.json

python3 -m build
