#!/usr/bin/env python3
"""
Finds and lists all processes that were started by bb_start.

When `bb_start` is used to start a process, it adds a `via=bb_start` to the
command line. You can also see the list of processes started by `bb_start` by
using `ps -ef | grep "via=bb_start"` from the terminal.

bb_ps is a script installed in the path by pip install of basic_bot.

usage:
```sh
bb_ps
```
"""
import psutil


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
                f"PID: {process.pid}, Name: {process.name()}, Command: {' '.join(process.cmdline())}"
            )
    else:
        print("No processes found with 'via=bb_start'.")


if __name__ == "__main__":
    main()
