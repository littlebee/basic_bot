import os

# print("Environment variables:")
# for name, value in os.environ.items():
#     print("{0}: {1}".format(name, value))


def env_string(name, default):
    env_val = os.getenv(name) or str(default)
    return env_val


def env_int(name, default):
    try:
        return int(env_string(name, default))
    except:
        return default


def env_float(name, default):
    try:
        return float(env_string(name, default))
    except:
        return default


def env_bool(name, default):
    value = env_string(name, default).lower()
    if value in ("true", "1"):
        return True
    else:
        return False


# Connect to central hub websocket
BB_HUB_PORT = env_int("BB_HUB_PORT", 5800)
BB_HUB_URI = f"ws://127.0.0.1:{BB_HUB_PORT}/ws"

BB_LOG_ALL_MESSAGES = env_bool("BB_LOG_ALL_MESSAGES", False)

# This is used to stub out the motor controller for testing and local (mac/windows) development
#   This is set to True in env vars on the raspberry pi by the default rc.local script
#
BB_ENV = env_string("BB_ENV", "development")
