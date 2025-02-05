import os
import time

from typing import List


def start_services(service_list: List[str]) -> None:
    """
    Starts requested subsystems as detached processes using same start script
    used to start on the bot.  This is useful for integration and e2e tests.

    BB_ENV=test is used to ensure that the services are started in the
    test environment which means motor control, vision camera, and other
    hardware specific modules are mocked.

    Args:

    - service_list = the names of the subsystems to start.  Which should be
        the base file names of the service main file in src/ directory.
    """

    for service_name in service_list:
        cmd = f'BB_ENV=test bb_start "{service_name}"'
        print(f"starting {service_name} with command: {cmd}")
        exit_code = os.system(cmd)
        assert exit_code == 0

    time.sleep(1)  # give all the services time to start


def stop_services(service_list: List[str]) -> None:
    """
    stops subsystems and restores the central hub state to what it was before the tests started

    Args:
        service_list = the names of the subsystems to start.  Which should be the base file names of the
                service main file in src/ directory.
    """

    for service_name in service_list:
        exit_code = os.system(f'BB_ENV=test bb_stop "{service_name}"')
        assert exit_code == 0
