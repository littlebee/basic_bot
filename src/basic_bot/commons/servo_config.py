"""
    Utility functions for reading and validating servo configuration from
    the `servo_config.yml` file.
"""

import yaml
from jsonschema import validate, ValidationError

from typing import TypedDict
from typing_extensions import NotRequired
from dataclasses import dataclass


from basic_bot.commons.servo_config_file_schema import servo_config_file_schema
from basic_bot.commons import constants as c, log


def validate_unique_names(config: dict) -> bool:
    servo_names = []
    for servo in config["servos"]:
        servo_name = servo["name"]
        if servo_name in servo_names:
            raise ValidationError(f"servo name {servo_name} is not unique")
        servo_names.append(servo_name)
    return True


def read_servo_config() -> dict:
    """
    Read and return the servo configuration from the `servo_config.yml` file.
    """
    try:
        log.info(f"Reading servo config from {c.BB_SERVO_CONFIG_FILE}")
        with open(c.BB_SERVO_CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)

            validate(config, servo_config_file_schema)
            validate_unique_names(config)
            return config
    except FileNotFoundError as e:
        log.error(f"Servo config file ({c.BB_SERVO_CONFIG_FILE}) not found. {e}")
        raise
    except yaml.YAMLError as e:
        log.info(
            f"Invalid YAML syntax for servo config file ({c.BB_SERVO_CONFIG_FILE}): {e}"
        )
        raise
    except ValidationError as e:
        log.info(f"Config file validation error: {e}")
        raise

    return config


class ServoOptions(TypedDict):
    name: str
    channel: int
    motor_range: NotRequired[int]
    min_angle: NotRequired[int]
    max_angle: NotRequired[int]
    min_pulse: NotRequired[int]
    max_pulse: NotRequired[int]


@dataclass
class ServoOptionsDefaults:
    motor_range: int = 180
    min_angle: int = 0
    max_angle: int = 180
    min_pulse: int = 500
    max_pulse: int = 2500
