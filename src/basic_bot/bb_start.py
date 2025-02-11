#!/usr/bin/env python3
"""
bb_start is a script to start services in the background. It reads a
list of services from the `basic_bot.yml` file unless a configuration
file is specified on the command line.

For each service started, bb_start writes the PID of the service to a
file in the 'pids' directory.  The PID file is used by the `bb_stop`.
`stdout` and `stderr` are redirected to a log files in the 'logs'
directory with the name of the service from the configuration file.


For more information on usage:
```sh
bb_start --help
```

"""
import argparse
import os
import subprocess
import time
import yaml
from jsonschema import validate, ValidationError


from basic_bot.commons.script_helpers.pid_files import is_pid_file_valid
from basic_bot.commons import constants as c


arg_parser = argparse.ArgumentParser(prog="bb_start", description=__doc__)
arg_parser.add_argument(
    "-f",
    "--file",
    help="configuration file from which to read services and configuration",
    default="./basic_bot.yml",
)


def validate_unique_names(config):
    service_names = []
    for service in config["services"]:
        service_name = service["name"]
        if service_name in service_names:
            raise ValidationError(f"Service name {service_name} is not unique")
        service_names.append(service_name)
    return True


def main() -> None:
    args = arg_parser.parse_args()

    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./pids", exist_ok=True)

    try:
        with open(args.file, "r") as f:
            config = yaml.safe_load(f)
        validate(config, config_file_schema)
        validate_unique_names(config)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}")
    except yaml.YAMLError:
        print(f"Error: Invalid YAML syntax: {args.file}")
    except ValidationError as e:
        print(f"Validation error: {e.message}")

    env_vars = config.get("env", {})
    env_vars.update(config.get(f"{c.BB_ENV}_env", {}))

    services = config["services"]
    print(f"starting {len(services)} services")

    for service in services:
        service_name = service["name"]
        log_file = service.get("log_file", f"./logs/{service_name}.log")
        pid_file = service.get("pid_file", f"./pids/{service_name}.pid")

        service_env = env_vars.copy()
        service_env.update(service.get("env", {}))
        service_env.update(service.get(f"{c.BB_ENV}_env", {}))

        if os.getenv("BB_ENV") == "test" or service_env.get("BB_ENV") == "test":
            print(f"running {service_name} in test mode")

        # if the pid file already exists, it may be currently
        # running, and we should not start another instance
        # because it will overwrite the pid file
        if is_pid_file_valid(pid_file):
            print(
                f"\nCowardly refusing to overwrite {pid_file}. try running:\n"
                f'bb_stop "{service_name}" \n\n'
                "from the terminal or if not, delete the pid file and try again.\n"
            )
            continue

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

        print(f"Starting {service_name}...")

        with open(log_file, "w") as log, open(pid_file, "w") as pid:
            process = subprocess.Popen(service["run"], stdout=log, stderr=log)
            time.sleep(0.5)
            if process.poll() is not None:
                print(f"Error starting service: {service}")
                log.write(f"Error starting service: {service}")
            else:
                pid.write(str(process.pid))
                print(
                    f"Started service: {service} and PID {process.pid} and logging to {log_file}"
                )


if __name__ == "__main__":
    main()
