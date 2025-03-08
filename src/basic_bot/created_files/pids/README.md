
This is where .pid files will show up.

When `bb_start` is run it will save the process id of the started service here in this directory. This is where `bb_stop` will look to determine the process id of the service to stop.

`bb_stop` will also remove pid files as it stops services.

