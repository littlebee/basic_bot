#!/usr/bin/env python3
import os
import sys
import signal

HELP = """
Usage: python3 -m basic_bot.stop [service] [service] ...

[service] is optional.  If not specified, all services listed in services.cfg in reverse order.
"""


def print_help():
    print(HELP)
    sys.exit(0)


def main():
    if len(sys.argv) > 1 and (sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        print_help()

    to_stop = []

    if len(sys.argv) > 1:
        to_stop = sys.argv[1:]
    else:
        with open("./services.cfg", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    to_stop.append(line)

    arraylength = len(to_stop)
    print(f"stopping {arraylength} services")

    # stop in reverse order as start
    for service in reversed(to_stop):
        start_cmd = service
        sub_system = start_cmd

        if start_cmd.startswith("-m "):
            sub_system = start_cmd[3:]

        print(f"stopping {sub_system}")

        base_name = os.path.basename(sub_system)
        log_file = f"./logs/{base_name}.log"
        pid_file = f"./pids/{base_name}.pid"

        if os.getenv("BB_ENV") == "test":
            print("stopping test mode process...")
            append = os.getenv("BB_FILE_APPEND", "")
            log_file = f"./logs/test_{base_name}{append}.log"
            pid_file = f"./pids/test_{base_name}{append}.pid"

        print(
            f"stopping {sub_system} at {os.popen('date').read().strip()}",
            file=open(log_file, "a"),
        )

        if os.path.isfile(pid_file):
            with open(pid_file, "r") as pidfile:
                pid = int(pidfile.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                    os.remove(pid_file)
                    print(f"Stopped service: {sub_system} with PID {pid}")
                except OSError as e:
                    print(f"kill failed for {sub_system}. \n {e}")
                    print(
                        f"Maybe retry using `sudo python3 -m basic_bot.stop` and if that fails, manually delete the .pid file at ({pid_file})"
                    )
        else:
            print(f"pid file not found for {sub_system} (skipping)")

    sys.exit(0)


if __name__ == "__main__":
    main()
