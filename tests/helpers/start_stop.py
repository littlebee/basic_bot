import os
import time

from typing import List

import helpers.constants as tc


def start_services(service_list: List[str]):
    """
    starts subsystems as a detached process using same start script used to start on the bot

    Args:
        service_list = the names of the subsystems to start.  Which should be the base file names of the
                service main file in src/ directory.
    """
    for service_name in service_list:
        cmd = f'BB_ENV=test BB_LOG_ALL_MESSAGES=1 BB_HUB_PORT={tc.CENTRAL_HUB_TEST_PORT} basic_bot_start "{service_name}"'
        print(f"starting {service_name} with command: {cmd}")
        exit_code = os.system(cmd)
        assert exit_code == 0
        time.sleep(1)


def stop_services(service_list: List[str]):
    """
    stops subsystems and restores the central hub state to what it was before the tests started

    Args:
        service_list = the names of the subsystems to start.  Which should be the base file names of the
                service main file in src/ directory.
    """

    for service_name in service_list:
        exit_code = os.system(f"BB_ENV=test basic_bot_stop {service_name}")
        assert exit_code == 0
