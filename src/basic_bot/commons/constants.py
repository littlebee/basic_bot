import os
import basic_bot.commons.env as env

# This is used to stub out the motor controller for testing and local (mac/windows) development
#   This is set to True in env vars on the raspberry pi by the default rc.local script
#
BB_ENV = env.env_string("BB_ENV", "development")

if BB_ENV == "test":
    # This is the port that the test central hub listens on
    BB_HUB_PORT = 5150
    BB_LOG_ALL_MESSAGES = True
else:
    BB_HUB_PORT = env.env_int("BB_HUB_PORT", 5100)
    BB_LOG_ALL_MESSAGES = env.env_bool("BB_LOG_ALL_MESSAGES", False)

# Connect to central hub websocket
BB_HUB_URI = f"ws://127.0.0.1:{BB_HUB_PORT}/ws"

# =============== Motor Control Service Constants
BB_MOTOR_I2C_ADDRESS = env.env_int("BB_MOTOR_I2C_ADDRESS", 0x60)
BB_LEFT_MOTOR_CHANNEL = env.env_int("BB_LEFT_MOTOR_CHANNEL", 1)
BB_RIGHT_MOTOR_CHANNEL = env.env_int("BB_RIGHT_MOTOR_CHANNEL", 2)

# =============== Vision service constants

BB_CAMERA_CHANNEL = env.env_int("BB_CAMERA_CHANNEL", 0)
BB_CAMERA_ROTATION = env.env_int("BB_CAMERA_ROTATION", 0)
BB_VISION_HEIGHT = env.env_int("BB_VISION_HEIGHT", 640)
BB_VISION_WIDTH = env.env_int("BB_VISION_WIDTH", 480)
# in degrees; depends on camera; RPi v2 cam is 62deg
BB_VISION_FOV = 62
# object detection threshold percentage; higher = greater confidence
BB_OBJECT_DETECTION_THRESHOLD = env.env_float("BB_OBJECT_DETECTION_THRESHOLD", 0.5)
# to enable the Coral USB TPU, you must use the tflite_detector and set this to True
BB_ENABLE_CORAL_TPU = env.env_bool("BB_ENABLE_CORAL_TPU", False)
# path to the directory containing the tflite model and labels
BB_TFLITE_DATA_DIR = env.env_string(
    "BB_TFLITE_DATA_DIR", os.path.join("models", "tflite")
)
# which model to use for object detection.  default is the model from the coral site
# which is faster than the model from the tensorflow hub
BB_TFLITE_MODEL = env.env_string(
    "BB_TFLITE_MODEL", "ssd_mobilenet_v1_coco_quant_postprocess.tflite"
)
# which model to use for object detection with BB_ENABLE_CORAL_TPU is true
BB_TFLITE_MODEL_CORAL = env.env_string(
    "BB_TFLITE_MODEL_CORAL",
    "ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite",
)
# number of threads to use for tflite detection
BB_TFLITE_THREADS = env.env_int("BB_TFLITE_THREADS", 2)
# http port used by the vision service for video streaming
BB_VISION_PORT = env.env_int("BB_VISION_PORT", 5801)
BB_DISABLE_RECOGNITION_PROVIDER = env.env_bool("BB_DISABLE_RECOGNITION_PROVIDER", False)

# ## See [issue #1](https://github.com/littlebee/scatbot-edge-ai-shootout/issues/1)
# ##    about support for pytorch

# Class labels from official PyTorch documentation for the pretrained model
# Note that there are some N/A's
# for complete list check https://tech.amikelive.com/node-718/what-object-categories-labels-are-in-coco-dataset/
# we will use the same list for this notebook
# BB_COCO_INSTANCE_CATEGORY_NAMES = [
#     "__background__",
#     "person",
#     "bicycle",
#     "car",
#     "motorcycle",
#     "airplane",
#     "bus",
#     "train",
#     "truck",
#     "boat",
#     "traffic light",
#     "fire hydrant",
#     "N/A",
#     "stop sign",
#     "parking meter",
#     "bench",
#     "bird",
#     "cat",
#     "dog",
#     "horse",
#     "sheep",
#     "cow",
#     "elephant",
#     "bear",
#     "zebra",
#     "giraffe",
#     "N/A",
#     "backpack",
#     "umbrella",
#     "N/A",
#     "N/A",
#     "handbag",
#     "tie",
#     "suitcase",
#     "frisbee",
#     "skis",
#     "snowboard",
#     "sports ball",
#     "kite",
#     "baseball bat",
#     "baseball glove",
#     "skateboard",
#     "surfboard",
#     "tennis racket",
#     "bottle",
#     "N/A",
#     "wine glass",
#     "cup",
#     "fork",
#     "knife",
#     "spoon",
#     "bowl",
#     "banana",
#     "apple",
#     "sandwich",
#     "orange",
#     "broccoli",
#     "carrot",
#     "hot dog",
#     "pizza",
#     "donut",
#     "cake",
#     "chair",
#     "couch",
#     "potted plant",
#     "bed",
#     "N/A",
#     "dining table",
#     "N/A",
#     "N/A",
#     "toilet",
#     "N/A",
#     "tv",
#     "laptop",
#     "mouse",
#     "remote",
#     "keyboard",
#     "cell phone",
#     "microwave",
#     "oven",
#     "toaster",
#     "sink",
#     "refrigerator",
#     "N/A",
#     "book",
#     "clock",
#     "vase",
#     "scissors",
#     "teddy bear",
#     "hair drier",
#     "toothbrush",
# ]
###


# Logging all the env variables in test for debugging
if BB_ENV == "test":
    print("Environment variables:")
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))
