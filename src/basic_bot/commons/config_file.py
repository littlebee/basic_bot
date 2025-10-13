"""
Utility function for reading and validating the basic_bot.yml configuration file.
"""

import os
import yaml
from jsonschema import validate, ValidationError
from basic_bot.commons.config_file_schema import config_file_schema
from basic_bot.commons import log


def read_config_file(file_path: str) -> dict:
    """
    Reads and validates the configuration file at the given path.

    Args:
        file_path (str): Path to the configuration file.

    Returns:
        dict: The configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
        jsonschema.ValidationError: If the configuration does not conform to the schema.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file {file_path} does not exist.")

        with open(file_path, "r") as file:
            try:
                config = yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file: {e}")

            validate(instance=config, schema=config_file_schema)

    except FileNotFoundError as e:
        log.error(f"Error: {file_path} config file not found. {e}")
        raise
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML syntax in {file_path}: {e}")
        raise
    except ValidationError as e:
        print(f"Config file validation error: {e}")
        raise

    return config
