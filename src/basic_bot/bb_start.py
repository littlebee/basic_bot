#!/usr/bin/env python3
import os
import sys
import subprocess
import time

HELP = """
Usage: python3 -m basic_bot.start [service] [service] ...

Where: [service] = the main python file file or module for the service
to start in the form of a relative path from the root of the project to
the src/*.py file.

If no services are specified, all services listed in services.cfg will be started.
Services will be started in the order they are listed in the file.

Example: python3 start.py basic_bot.services.central_hub
"""


def print_help():
    print(HELP)
    sys.exit(0)


def main():

    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print_help()

    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./pids", exist_ok=True)

    to_start = []

    # comment this out to stop all services from logging every message
    # sent or received
    os.environ["LOG_ALL_MESSAGES"] = "1"

    if len(sys.argv) > 1:
        to_start = sys.argv[1:]
    else:
        with open("./services.cfg", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    to_start.append(line)

    arraylength = len(to_start)
    print(f"starting {arraylength} services")

    for service in to_start:
        sub_system = service
        is_module = False

        if service.startswith("-m "):
            is_module = True
            sub_system = service[3:]

        base_name = os.path.basename(sub_system)
        log_file = f"./logs/{base_name}.log"
        pid_file = f"./pids/{base_name}.pid"

        # if the pid file already exists, it may be currently
        # running, and we should not start another instance
        # because it will overwrite the pid file
        if os.path.exists(pid_file):
            print(
                f"\nCowardly refusing to overwrite {pid_file}. \n"
                f"Is {sub_system} already running? If so,  try running \n\n"
                f'bb_stop "-m {sub_system}" \n\n'
                "from the terminal or if not, delete the pid file and try again.\n"
            )
            continue

        if os.getenv("BB_ENV") == "test":
            print(f"running {sub_system} in test mode")
            append = os.getenv("BB_FILE_APPEND", "")
            log_file = f"./logs/test_{base_name}{append}.log"
            pid_file = f"./pids/test_{base_name}{append}.pid"

        # if the log_file already exists, rotate up to 3 times
        # appending a .number to the end of the file name
        for i in range(3, 0, -1):
            old_log_file = f"{log_file}.{i - 1}" if i > 1 else log_file
            new_log_file = f"{log_file}.{i}"
            if not os.path.exists(old_log_file):
                continue
            if os.path.exists(new_log_file):
                os.remove(new_log_file)
            os.rename(old_log_file, new_log_file)

        print(f"Starting {sub_system}...")

        args = ["python", "-m", sub_system] if is_module else ["python3", sub_system]

        with open(log_file, "w") as log, open(pid_file, "w") as pid:
            process = subprocess.Popen(args, stdout=log, stderr=log)
            pid.write(str(process.pid))
            print(
                f"Started service: {service} and PID {process.pid} and logging to {log_file}"
            )

        if sub_system == "basic_bot.services.central_hub":
            # let the central hub start up before starting the remaining services
            time.sleep(1)


if __name__ == "__main__":
    main()
