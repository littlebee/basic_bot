#!/usr/bin/env python3
"""
`bb_stop` is a script to stop basic_bot services started with `bb_start`

The services to stop are read from the `basic_bot.yml` file unless a
`--file filename` is specified on the command line.


For more information on usage:
```sh
bb_stop --help
```

"""
import argparse
import os
import signal
import yaml
from jsonschema import validate, ValidationError

from typing import Optional, List


from basic_bot.commons.script_helpers.pid_files import is_pid_file_valid
from basic_bot.commons.script_helpers.log_files import get_log_time
from basic_bot.commons.config_file_schema import config_file_schema


arg_parser = argparse.ArgumentParser(prog="bb_stop", description=__doc__)
arg_parser.add_argument(
    "-f",
    "--file",
    help="configuration file from which to read services and configuration",
    default="./basic_bot.yml",
)
arg_parser.add_argument(
    "-s",
    "--services",
    help="comma separated list of services to start",
    default=None,
)


def stop_service(
    service_name: str,
    log_file: Optional[str],
    pid_file: Optional[str],
) -> None:
    log_file = log_file or f"./logs/{service_name}.log"
    pid_file = pid_file or f"./pids/{service_name}.pid"

    # if the pid file already exists, it may be currently
    # running, and we should not start another instance
    # because it will overwrite the pid file
    if not is_pid_file_valid(pid_file):
        print(
            f"WARN: Service {service_name} is not running or o PID file: {pid_file} not found.  Skipping"
        )
        try:
            os.remove(pid_file)
        except FileNotFoundError:
            pass
        return

    print(f"Stopping service: {service_name}")

    with open(log_file, "a") as log:
        log.write(f"{get_log_time()}: Stopping service: {service_name}\n")

    with open(pid_file, "r") as f:
        pid = f.read().strip()
        print(f"Sending SIGTERM to service {service_name} with PID: {pid}")
        os.kill(int(pid), signal.SIGTERM)

    os.remove(pid_file)


def stop_services(config: dict, services_filter: Optional[List[str]] = None) -> None:
    for service in config["services"]:
        if services_filter and service["name"] not in services_filter:
            continue

        stop_service(
            service["name"],
            service.get("log_file"),
            service.get("pid_file"),
        )


def main() -> None:
    args = arg_parser.parse_args()

    try:
        with open(args.file, "r") as f:
            config = yaml.safe_load(f)
        validate(config, config_file_schema)

        services_filter = None
        if args.services:
            services_filter = args.services.split(",")

        stop_services(config, services_filter)

    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
    except yaml.YAMLError:
        print(f"Error: Invalid YAML syntax: {args.file}")
    except ValidationError as e:
        print(f"Config file validation error: {e.message}")


if __name__ == "__main__":
    main()
