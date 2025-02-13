#!/usr/bin/env python3
"""
Finds all processes started by bb_start and kills them with signal 15.
It also removes all files in the local pids directory.

usage:
```sh
python -m src.basic_bot.debug.killall_bb_procs
```
"""
import os
import psutil
import signal

if __name__ == "__main__":
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
