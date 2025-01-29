"""
Simple methods for logging messages to console with timestamps
and "INFO", "DEBUG", "ERROR" prefixes.

These methods ensure that the last message is flushed to console.

`bb_start`, which is used to run services in the background, will
redirect all stdout and stderr to a log file.

"""

import datetime
import sys

import basic_bot.commons.constants as c


def debug(message: str) -> None:
    """Flush DEBUG: message to console only in development and test environments"""
    if c.BB_ENV in ["development", "test"]:
        print(f"{datetime.datetime.now():%Y%m%d-%H%M%S} DEBUG: {message}")
        sys.stdout.flush()


def info(message: str) -> None:
    """Flush INFO: message to console"""
    print(f"{datetime.datetime.now():%Y%m%d-%H%M%S} INFO: {message}")
    sys.stdout.flush()


def error(message: str) -> None:
    """Flush ERROR: message to console"""
    print(f"{datetime.datetime.now():%Y%m%d-%H%M%S} ERROR: {message}")
    sys.stdout.flush()
