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


import basic_bot.commons.env as env

BB_ENV = env.env_string("BB_ENV", "development")
"""
Test runner will set this to "test".

Set this to "production" on the onboard computer to run the bot in production
mode.  See [Getting Started Guide](https://littlebee.github.io/basic_bot/#add-bb_env-export)
for more information.
"""

BB_LOG_ALL_MESSAGES = env.env_bool("BB_LOG_ALL_MESSAGES", False)
"""
Set this to True to log all messages sent and received by services to
each of their respective log files.
"""

BB_HUB_HOST = env.env_string("BB_HUB_HOST", "127.0.0.1")
"""
The websocket host that the central hub is running.
"""

BB_HUB_PORT = hub_port = env.env_int("BB_HUB_PORT", 5100)
"""
The websocket port that the central_hub service listens on.
"""

# Connect to central hub websocket
BB_HUB_URI = f"ws://{BB_HUB_HOST}:{BB_HUB_PORT}/ws"
"""
This is the full URI to connect to the central_hub service websocket.
"""

# =============== Motor Control Service Constants

BB_MOTOR_I2C_ADDRESS = env.env_int("BB_MOTOR_I2C_ADDRESS", 0x60)
"""
Used by basic_bot.services.motor_control_2w to connect to the i2c
motor controller.
"""

BB_LEFT_MOTOR_CHANNEL = env.env_int("BB_LEFT_MOTOR_CHANNEL", 1)
"""
default: 1
"""

BB_RIGHT_MOTOR_CHANNEL = env.env_int("BB_RIGHT_MOTOR_CHANNEL", 2)
"""
default: 2
"""

# =============== Servo Service Constants
BB_SERVO_CONFIG_FILE = env.env_string("BB_SERVO_CONFIG_FILE", "./servo_config.yml")
"""
See api docs for servo control services
"""

# =============== System Stats Service Constants
BB_SYSTEM_STATS_SAMPLE_INTERVAL = env.env_float("BB_SYSTEM_STATS_SAMPLE_INTERVAL", 1)
"""
In seconds, the interval at which the system stats service samples the system
and publishes system stats to the central hub.
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
The camera channel to use. 0 is the default camera.
"""

BB_CAMERA_ROTATION = env.env_int("BB_CAMERA_ROTATION", 0)
"""
The camera rotation in degrees. 0 is the default rotation.
"""

BB_CAMERA_FPS = env.env_int("BB_CAMERA_FPS", 30)
"""
The camera setting frames per second.
"""

BB_VISION_WIDTH = env.env_int("BB_VISION_WIDTH", 640)
"""
In pixels, this is the width of the camera frame to capture.
"""

BB_VISION_HEIGHT = env.env_int("BB_VISION_HEIGHT", 480)
"""
In pixels, this is the height of the camera frame to capture.

"""

BB_VISION_FOV = 62
"""
The field of view of the camera in degrees.  Depends on camera;
RPi v2 cam is 62 deg.
"""

BB_OBJECT_DETECTION_THRESHOLD = env.env_float("BB_OBJECT_DETECTION_THRESHOLD", 0.5)
"""
The object detection threshold percentage 0 - 1; higher = greater confidence.
"""

# to enable the Coral USB TPU, you must use the tflite_detector and set this to True
BB_ENABLE_CORAL_TPU = env.env_bool("BB_ENABLE_CORAL_TPU", False)
"""
Set this to True to enable the Coral USB TPU for object detection.
"""

BB_TFLITE_MODEL = env.env_string(
    "BB_TFLITE_MODEL", "./models/tflite/ssd_mobilenet_v1_coco_quant_postprocess.tflite"
)
"""
Which model to use for object detection when BB_ENABLE_CORAL_TPU is false.
Default is the model from the coral site which is faster than the model
from the tensorflow hub
"""

BB_TFLITE_MODEL_CORAL = env.env_string(
    "BB_TFLITE_MODEL_CORAL",
    "./models/tflite/ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite",
)
"""
Which model to use for object detection when BB_ENABLE_CORAL_TPU is true.
"""

# number of threads to use for tflite detection
BB_TFLITE_THREADS = env.env_int("BB_TFLITE_THREADS", 3)
"""
Number of threads to use for tflite detection.  Testing object detection
on a Rasberry PI 5, without any other CPU or memory pressure, 4 tflite threads
was only 1 fps faster (29.5fps) than 3 threads (28.6fps).  2 threads was 22fps.

Warning: Setting this too high can actually reduce the object detection  frame rate.
In the case of daphbot_due, which has a [pygame based onboard UI service](https://github.com/littlebee/daphbot-due/blob/main/src/onboard_ui_service.py)
that has a configurable render frame rate, the tflite detection running on 4 threads
was reduced to about 12 fps when the render frame rate was set to 30fps.
"""

BB_VISION_HOST = env.env_string("BB_VISION_HOST", "127.0.0.1")
"""
The IP address that the vision service is running on for REST api and video streaming.
"""

BB_VISION_PORT = env.env_int("BB_VISION_PORT", 5802 if BB_ENV == "test" else 5801)
"""
The HTTP port that the vision service listens on for video streaming and REST api.
"""

BB_VISION_URI = env.env_string(
    "BB_VISION_URI", f"http://{BB_VISION_HOST}:{BB_VISION_PORT}"
)
"""
The full URI to connect to the vision service REST and video streaming.
"""


BB_DISABLE_RECOGNITION_PROVIDER = env.env_bool("BB_DISABLE_RECOGNITION_PROVIDER", False)
"""
Set this to True to disable the recognition provider.
"""

BB_VIDEO_PATH = env.env_string("BB_VIDEO_PATH", "./recorded_video")
"""
The path where the vision service saves recorded video.
"""
