"""
basic_bot.commons.constants can be imported to access the constants used
by basic_bot services. The constants are set by default and
all can be overridden by setting environment variables.

If you are using bb_start to start the services, you can set the
BB_ environment variables in the basic_bot.yml file.
See the [bb_start documentation](https://littlebee.github.io/basic_bot/Api%20Docs/scripts/bb_start/)

"""

#
#  Development Note:  If you change the name of the this file, or
#   it's relative path, you will need to update the /build_docs.py script
#


import os
import basic_bot.commons.env as env

BB_ENV = env.env_string("BB_ENV", "development")
"""
Default: "development"

Test runner should set this to "test".

Set this to "production" on the onboard computer to run the bot in production
mode.
"""

if BB_ENV == "test":
    # This is the port that the test central hub listens on
    hub_port = 5150
    log_all = True
else:
    hub_port = env.env_int("BB_HUB_PORT", 5100)
    log_all = env.env_bool("BB_LOG_ALL_MESSAGES", False)

BB_LOG_ALL_MESSAGES = log_all
"""
    Default: True when BB_ENV=test; false otherwise

    Set this to True to log all messages sent and received by services to
    each of their respective log files.
"""


BB_HUB_PORT = hub_port
"""
    Default: 5150 when BB_ENV=test; 5100 otherwise

    This is the port that the central hub listens on.
"""

BB_LOG_ALL_MESSAGES = log_all
"""
    Default: True when BB_ENV=test; false otherwise

    Set this to True to log all messages sent and received by services.
"""

# Connect to central hub websocket
BB_HUB_URI = f"ws://127.0.0.1:{BB_HUB_PORT}/ws"
"""
    Default: `f"ws://127.0.0.1:{BB_HUB_PORT}/ws"`

"""


# =============== Motor Control Service Constants
BB_MOTOR_I2C_ADDRESS = env.env_int("BB_MOTOR_I2C_ADDRESS", 0x60)
"""
    default: 0x60

    Used by basic_bot.services.motor_control_2w to connect to the
    i2c motor controller.
"""
BB_LEFT_MOTOR_CHANNEL = env.env_int("BB_LEFT_MOTOR_CHANNEL", 1)
"""
    default: 1
"""
BB_RIGHT_MOTOR_CHANNEL = env.env_int("BB_RIGHT_MOTOR_CHANNEL", 2)
"""
    default: 2
"""

# =============== System Stats Service Constants
BB_SYSTEM_STATS_SAMPLE_INTERVAL = env.env_float("BB_SYSTEM_STATS_SAMPLE_INTERVAL", 0.5)
"""
    In seconds, the interval at which the system stats service samples the system
    and publishes system stats to the central hub.

    default: 0.5 (~2Hz)
"""


# =============== Vision service constants
default_camera_module = (
    "basic_bot.test_helpers.camera_mock"
    if BB_ENV == "test"
    else "basic_bot.commons.camera_opencv"
)
# see other supported camera modules in basic_bot.commons.camera_*
# for example, `BB_CAMERA_MODULE=basic_bot.commons.camera_picamera`
BB_CAMERA_MODULE = env.env_string("BB_CAMERA_MODULE", default_camera_module)
"""
    default: "basic_bot.commons.camera_opencv" or
        "basic_bot.test_helpers.camera_mock" when BB_ENV=test

    When using a ribbon cable camera on a Raspberry Pi 4/5, set this to
    "basic_bot.commons.camera_picamera".
"""

BB_CAMERA_CHANNEL = env.env_int("BB_CAMERA_CHANNEL", 0)
"""
    default: 0

    This is the camera channel to use. 0 is the default camera.
"""

BB_CAMERA_ROTATION = env.env_int("BB_CAMERA_ROTATION", 0)
"""
    default: 0

    This is the camera rotation in degrees. 0 is the default rotation.
"""

BB_CAMERA_FPS = env.env_int("BB_CAMERA_FPS", 30)
"""
    default: 30

    This is the camera setting frames per second.
"""

BB_VISION_WIDTH = env.env_int("BB_VISION_WIDTH", 640)
"""
    default: 640

    In pixels, this is the width of the camera frame to capture.
"""

BB_VISION_HEIGHT = env.env_int("BB_VISION_HEIGHT", 480)
"""
    default: 480

    In pixels, this is the height of the camera frame to capture.

"""

BB_VISION_FOV = 62
"""
    default: 62

    This is the field of view of the camera in degrees.
    Depends on camera; RPi v2 cam is 62deg.
"""

BB_OBJECT_DETECTION_THRESHOLD = env.env_float("BB_OBJECT_DETECTION_THRESHOLD", 0.5)
"""
    default: 0.5

    This is the object detection threshold percentage 0 - 1; higher = greater confidence.
"""

# to enable the Coral USB TPU, you must use the tflite_detector and set this to True
BB_ENABLE_CORAL_TPU = env.env_bool("BB_ENABLE_CORAL_TPU", False)
"""
    default: False

    Set this to True to enable the Coral USB TPU for object detection.
"""

BB_TFLITE_MODEL = env.env_string(
    "BB_TFLITE_MODEL", "./models/tflite/ssd_mobilenet_v1_coco_quant_postprocess.tflite"
)
"""
    default: "./models/tflite/ssd_mobilenet_v1_coco_quant_postprocess.tflite"

    Which model to use for object detection when BB_ENABLE_CORAL_TPU is false.
    Default is the model from the coral site which is faster than the model
    from the tensorflow hub
"""

BB_TFLITE_MODEL_CORAL = env.env_string(
    "BB_TFLITE_MODEL_CORAL",
    "./models/tflite/ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite",
)
"""
    default: "./models/tflite/ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite"

    Which model to use for object detection when BB_ENABLE_CORAL_TPU is true.
"""

# number of threads to use for tflite detection
BB_TFLITE_THREADS = env.env_int("BB_TFLITE_THREADS", 2)
"""
    default: 2

    Number of threads to use for tflite detection.
"""

# http port used by the vision service for video streaming
port = 5802 if BB_ENV == "test" else 5801
BB_VISION_PORT = env.env_int("BB_VISION_PORT", port)
"""
    default: 5802 when BB_ENV=test; 5801 otherwise

    This is the HTTP port that the vision service listens  on for video
    streaming and REST api.
"""

BB_DISABLE_RECOGNITION_PROVIDER = env.env_bool("BB_DISABLE_RECOGNITION_PROVIDER", False)
"""
    default: False

    Set this to True to disable the recognition provider.
"""


# Logging all the env variables in test for debugging
if BB_ENV == "test":
    print("Environment variables:")
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))
