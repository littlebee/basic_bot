#!/usr/bin/env python3

# Finds all processes matching "python -m basic_bot.*" and kills
# them with signal 15
import psutil

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
        print("Found processes started by bb_start:")
        for process in matching_processes:
            print(
                f"PID: {process.pid}, Name: {process.name()}, Command: {' '.join(process.cmdline())}"
            )
    else:
        print("No processes found matching the regex.")
