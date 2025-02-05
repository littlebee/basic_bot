"""
This diagnostic script will test the installation and setup of the Google
[ai-edge-litert](https://ai.google.dev/edge/litert/inference#run-python)

It uses opencv to open the test image file and then runs the model inference on the image.

Needs to have ai-edge-litert from Google installed:
```sh
python -m pip install ai-edge-litert
```
Unfortunately the package will not install on Macs or Windows.  It will install on
Linux and Raspberry Pi (arm64).

`ai-edge-litert` is suppose to be the future replacement of the tflite_runtime package.

Usage:
```sh
python -m src.basic_bot.debug.test_ai-edge-litert
```
"""

import os
import cv2
from PIL import Image
from PIL import ImageFont, ImageDraw
import numpy as np

from ai_edge_litert.interpreter import Interpreter  # type: ignore

from basic_bot.commons.coco_lables import coco_lables as labels

test_image = os.path.join(os.path.dirname(__file__), "testdata", "daphne.jpg")
model_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "created_files",
        "models",
        "tflite",
        "ssd_mobilenet_v1_coco_quant_postprocess.tflite",
    )
)
print(f"{test_image=}")
print(f"{model_path=}")

print(f"loading model: {model_path}")
interpreter = Interpreter(model_path=model_path)
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
initial_h, initial_w, channels = img.shape
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


img = Image.open(test_image)  # type: ignore
draw = ImageDraw.Draw(img, "RGBA")
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
img.save(output_file)
print("Saved to ", output_file)
