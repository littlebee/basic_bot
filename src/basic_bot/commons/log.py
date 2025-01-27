import datetime
import sys

import basic_bot.commons.constants as c


def debug(message: str) -> None:
    """Flush debug message to console only in development and test environments"""
    if c.BB_ENV in ["development", "test"]:
        print(f"{datetime.datetime.now():%Y%m%d-%H%M%S} DEBUG: {message}")
        sys.stdout.flush()


def info(message: str) -> None:
    """Flush message to console"""
    print(f"{datetime.datetime.now():%Y%m%d-%H%M%S} INFO: {message}")
    sys.stdout.flush()


def error(message: str) -> None:
    """Flush error message to console"""
    print(f"{datetime.datetime.now():%Y%m%d-%H%M%S} ERROR: {message}")
    sys.stdout.flush()
