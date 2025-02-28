#!/usr/bin/env python3
"""
bb_start is a script to start services in the background. It reads a
list of services from the `basic_bot.yml` file unless a
`--file filename` is specified on the command line.

For each service in the config file, bb_start:

- starts the service in the background detached from the terminal.
- writes the PID of the service to a file in the 'pids' directory.
The PID file is used by the `bb_stop`.
- rotates log files for each service.  If the log file already exists,
it is renamed to `service_name.log.1` and the previous is `...log.2`, etc.
- `stdout` and `stderr` are redirected to a log files in the 'logs'
directory with the name of the service from the configuration file.


For more information on usage:
```sh
bb_start --help
```

"""
import argparse
import os
import shlex
import subprocess
import time
import traceback
import yaml
from jsonschema import validate, ValidationError


from typing import Optional, Dict, List


from basic_bot.commons.script_helpers.pid_files import is_pid_file_valid
from basic_bot.commons.script_helpers.log_files import get_log_time
from basic_bot.commons.config_file_schema import config_file_schema
from basic_bot.commons import constants as c


arg_parser = argparse.ArgumentParser(prog="bb_start", description=__doc__)
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


def validate_unique_names(config):
    service_names = []
    for service in config["services"]:
        service_name = service["name"]
        if service_name in service_names:
            raise ValidationError(f"Service name {service_name} is not unique")
        service_names.append(service_name)
    return True


def rotate_log_files(log_file: str) -> None:
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


def start_service(
    service_name: str,
    run_cmd: str,
    log_file: Optional[str] = None,
    pid_file: Optional[str] = None,
    service_env: Dict[str, str] = {},
) -> None:
    log_file = log_file or f"./logs/{service_name}.log"
    pid_file = pid_file or f"./pids/{service_name}.pid"

    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./pids", exist_ok=True)

    if os.getenv("BB_ENV") == "test":
        print(f"running {service_name} in test mode")

    # if the pid file already exists, it may be currently
    # running, and we should not start another instance
    # because it will overwrite the pid file
    if is_pid_file_valid(pid_file):
        print(
            f"\nCowardly refusing to overwrite {pid_file}. try running:\n"
            f'bb_stop "{service_name}" \n\n'
            "from the terminal or, if not, delete the pid file and try again.\n"
        )
        return

    rotate_log_files(log_file)

    print(f"Starting service: {run_cmd} with env: {service_env}")
    args = shlex.split(run_cmd)
    # this can be used to identify processes started by bb_start like:
    # `ps aux | grep via=bb_start``
    args.append("via=bb_start")
    # must include full environment if env arg to Popen is used
    env = {**os.environ, **service_env}
    # print(f" Combined env: {env}")

    with open(log_file, "w") as log:
        process = subprocess.Popen(args, stdout=log, stderr=log, env=env)
        log_ts = get_log_time()
        time.sleep(0.5)
        if process.poll() is not None:
            print(f"Error starting service: {service_name}")
            log.write(f"{log_ts}: Error starting service: {service_name}")
        else:
            with open(pid_file, "w") as f:
                f.write(str(process.pid))
            print(
                f"{log_ts}: Started service: {service_name} and PID {process.pid} and logging to {log_file}"
            )


def start_services(config: dict, services_filter: Optional[List[str]] = None):
    env_vars = config.get("env", {})
    env_vars.update(config.get(f"{c.BB_ENV}_env", {}))

    for service in config["services"]:
        if services_filter and service["name"] not in services_filter:
            continue
        service_env = env_vars.copy()
        service_env.update(service.get("env", {}))
        service_env.update(service.get(f"{c.BB_ENV}_env", {}))
        start_service(
            service["name"],
            service["run"],
            service.get("log_file"),
            service.get("pid_file"),
            service_env,
        )


def main() -> None:
    args = arg_parser.parse_args()

    try:
        with open(args.file, "r") as f:
            config = yaml.safe_load(f)
        validate(config, config_file_schema)
        validate_unique_names(config)

        services_filter = None
        if args.services:
            services_filter = args.services.split(",")

        start_services(config, services_filter)

    except FileNotFoundError as e:
        print(f"Error: File not found. {e}")
        traceback.print_exc()
    except yaml.YAMLError:
        print(f"Error: Invalid YAML syntax: {args.file}")
    except ValidationError as e:
        print(f"Config file validation error: {e}")


if __name__ == "__main__":
    main()
