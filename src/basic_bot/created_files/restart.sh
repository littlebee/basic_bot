
#!/bin/sh

echo "Stopping services...
bb_stop $@

echo "Sleeping for 5 seconds"
sleep 5

if [ $# -eq 0 ]; then
    bb_killall
    sleep 2
fi

echo "Starting services..."
bb_start $@
