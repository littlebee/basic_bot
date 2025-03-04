"""
This module contains the schema for the configuration file that the
servo services read.

It can be used with jsonvalidate to validate the configuration file.
"""

servo_config_file_schema = {
    "type": "object",
    "required": ["servos"],
    "properties": {
        "servos": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "channel"],
                "properties": {
                    #
                    # Must have unique name for each servo.
                    "name": {"type": "string"},
                    #
                    # The channel on the PCA9685 board that the servo is connected to.
                    "channel": {"type": "integer"},
                    #
                    # The total manufacturer's range of the servo in degrees.
                    "motor_range": {"type": "integer"},
                    #
                    # The minimum angle that the servo should be constrained.
                    "min_angle": {"type": "integer"},
                    #
                    # The maximum angle that the servo should be constrained.
                    "max_angle": {"type": "integer"},
                    #
                    # The minimum pulse width in microseconds that the servo will accept
                    # as specified by the manufacturer.
                    "min_pulse": {"type": "integer"},
                    #
                    # The maximum pulse width in microseconds that the servo will accept
                    # as specified by the manufacturer.
                    "max_pulse": {"type": "integer"},
                },
            },
        },
    },
}
