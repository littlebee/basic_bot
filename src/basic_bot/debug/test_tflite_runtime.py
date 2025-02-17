"""
Tests that the TensorFlow Lite runtime is installed and working.

Usage:
```sh
python -m basic_bot.debug.test_tflite_runtime
```

Must have TensorFlow Lite installed.  From your Python virtual environment:
```sh
python -m pip install tflite-runtime
```
The above may fail on mac (apple silicon) and windows.  It should work on Ubuntu Linux and Raspberry Pi.

src:
https://www.hackster.io/news/benchmarking-tensorflow-and-tensorflow-lite-on-raspberry-pi-5-b9156d58a6a2
https://github.com/aallan/benchmarking-ml-on-the-edge/blob/98467e058732a6626b6fb382980477b2121b34d2/benchmark_tf.py#L115

"""

import os
import cv2
import numpy as np

import tflite_runtime.interpreter as tflite  # type: ignore

from PIL import Image
from PIL import ImageFont, ImageDraw


from basic_bot.commons.coco_lables import coco_lables as labels

test_image = os.path.join(os.path.dirname(__file__), "testdata", "daphne.jpg")
model_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "commons",
        "models",
        "tflite",
        "ssd_mobilenet_v1_coco_quant_postprocess.tflite",
    )
)
print(f"{test_image=}")
print(f"{model_path=}")

print("Loading model and tensors...")
# Load TFLite model and allocate tensors.
interpreter = tflite.Interpreter(model_path=model_path, num_threads=4)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]["shape"][1]
width = input_details[0]["shape"][2]
floating_model = False
if input_details[0]["dtype"] == np.float32:
    floating_model = True


print("reading test image")
img = cv2.imread(test_image)
initial_h, initial_w, channels = img.shape  # type: ignore
frame = cv2.resize(img, (width, height))

input_data = np.expand_dims(frame, axis=0)
if floating_model:
    input_data = (np.float32(input_data) - 127.5) / 127.5  # type: ignore
interpreter.set_tensor(input_details[0]["index"], input_data)

print("Running inference...")
interpreter.invoke()

detected_boxes = interpreter.get_tensor(output_details[0]["index"])
detected_classes = interpreter.get_tensor(output_details[1]["index"])
detected_scores = interpreter.get_tensor(output_details[2]["index"])
num_boxes = interpreter.get_tensor(output_details[3]["index"])


editable_img = Image.open(test_image)
draw = ImageDraw.Draw(editable_img, "RGBA")
font_file = model_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "testdata", "Helvetica.ttf")
)
helvetica = ImageFont.truetype(font_file, size=72)


# print(f"Done. {detected_boxes=}, {detected_classes=}, {detected_scores=}, {num_boxes=}")
# Function to draw a rectangle with width > 1
def draw_rectangle(draw, coordinates, color, width=1):
    for i in range(width):
        rect_start = (coordinates[0] - i, coordinates[1] - i)
        rect_end = (coordinates[2] + i, coordinates[3] + i)
        draw.rectangle((rect_start, rect_end), outline=color, fill=color)


for i in range(int(num_boxes)):
    top, left, bottom, right = detected_boxes[0][i]
    classId = int(detected_classes[0][i])
    score = detected_scores[0][i]
    if score > 0.5:
        xmin = left * initial_w
        ymin = bottom * initial_h
        xmax = right * initial_w
        ymax = top * initial_h
        box = [xmin, ymin, xmax, ymax]
        class_name = labels[classId]

        print(f"found {class_name} {score=}, {box=} ")

        draw_rectangle(draw, box, (0, 128, 128, 20), width=5)
        draw.text(
            (box[0] + 20, box[1] + 20),
            labels[classId],
            fill=(255, 255, 255, 20),
            font=helvetica,
        )

output_file = os.path.join(os.getcwd(), "tflite_runtime_test_output.jpg")
editable_img.save(output_file)
print("Saved to ", output_file)
