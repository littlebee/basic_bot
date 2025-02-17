import os

from typing import Tuple, Mapping

from basic_bot import bb_start, bb_stop


def get_files_for_service(service_name: str) -> Tuple[str, str]:
    log_file = os.path.join(os.getcwd(), "logs", f"test_{service_name}.log")
    pid_file = os.path.join(os.getcwd(), "pids", f"test_{service_name}.pid")
    return log_file, pid_file


def start_service(service_name: str, run_cmd: str, env: Mapping[str, str] = {}) -> None:
    """
    Starts requested service using bb_start command.  This is useful
    for integration and e2e tests.

    BB_ENV=test is forced to ensure that the services are started in the
    test environment which means motor control, vision camera, and other
    hardware specific modules are mocked.

    Args:

        service_name = the name of the service. "test_" is prepended to the
            service name to create pid and and log files that are distinct from
            the services which may be running for development.

        run_cmd = the command to start the service.
    """
    updated_env: Mapping[str, str] = {**env, "BB_ENV": "test"}
    log_file, pid_file = get_files_for_service(service_name)
    bb_start.start_service(
        f"test_{service_name}", run_cmd, log_file, pid_file, updated_env
    )


def stop_service(service_name) -> None:
    """
    stops the requested service using bb_stop command.

    Args:
        service_name: the name of the service to stop as it was passed to
            start_service function above
    """
    log_file, pid_file = get_files_for_service(service_name)
    bb_stop.stop_service(f"test_{service_name}", log_file, pid_file)
