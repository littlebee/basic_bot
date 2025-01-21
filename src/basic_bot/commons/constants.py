import os
import basic_bot.commons.env as env


# Connect to central hub websocket
BB_HUB_PORT = env.env_int("BB_HUB_PORT", 5800)
BB_HUB_URI = f"ws://127.0.0.1:{BB_HUB_PORT}/ws"

BB_LOG_ALL_MESSAGES = env.env_bool("BB_LOG_ALL_MESSAGES", False)

# This is used to stub out the motor controller for testing and local (mac/windows) development
#   This is set to True in env vars on the raspberry pi by the default rc.local script
#
BB_ENV = env.env_string("BB_ENV", "development")

# Motor Control Constants
BB_MOTOR_I2C_ADDRESS = env.env_int("BB_MOTOR_I2C_ADDRESS", 0x60)
BB_LEFT_MOTOR_CHANNEL = env.env_int("BB_LEFT_MOTOR_CHANNEL", 1)
BB_RIGHT_MOTOR_CHANNEL = env.env_int("BB_RIGHT_MOTOR_CHANNEL", 2)

if BB_ENV == "test":
    print("Environment variables:")
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))
