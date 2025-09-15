#!/bin/sh
echo "Stopping services..."
bb_stop $@
echo "Sleeping for 2 seconds"
sleep 2
echo "Starting services..."
bb_start $@
