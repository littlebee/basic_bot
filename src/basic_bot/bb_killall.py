#!/usr/bin/env python3
"""
Finds all processes started by bb_start and kills them with signal 15.
It also removes all files in the local pids directory if they exist.

This script differs from `bb_stop` in that it works more like the *nix
`killall` command, which sends a signal to all processes that match a
query.   It does not discriminate based on any `basic_bot.yml` file
like `bb_stop` does.

See also: `bb_ps` script.

bb_killall is a script installed in the path by pip install of basic_bot.

usage:
```sh
bb_killall
```
"""
import os
import psutil
import signal


def main():
    matching_processes = []
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdLine = str(process.info.get("cmdline"))
            if cmdLine:
                # print("looking at: ", cmdLine)
                if "via=bb_start" in cmdLine:
                    matching_processes.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if matching_processes:
        for process in matching_processes:
            print(
                f"Killing PID: {process.pid}, Name: {process.name()}, Command: {' '.join(process.cmdline())}"
            )
            process.send_signal(signal.SIGTERM)

    else:
        print("No processes found matching the regex.")

    # remove all files in the pids directory
    for pid_file in os.listdir("./pids"):
        os.remove(f"./pids/{pid_file}")


if __name__ == "__main__":
    main()
