#!/usr/bin/env python3
"""
This diagnostic script will test the installation of open cv,
the ability to read an image from a file, the ability to add
text to the image, and the ability to save an image to a file.


usage:
```sh
python -m src.basic_bot.debug.test_opencv_img
```

"""

import os
import cv2

test_image = os.path.join(os.path.dirname(__file__), "testdata", "daphne.jpg")
output_file = os.path.join(os.getcwd(), "opencv_img_test_output.jpg")

print(f"reading test image: {test_image}")
img = cv2.imread(test_image)

# pretty sure this is a picture of daphne :), let's label it such
labeled_image = cv2.putText(
    img, "Daphne!", (200, 400), cv2.FONT_HERSHEY_SIMPLEX, 5, (128, 0, 255), 20
)

print(f"saving labeled image to {output_file}")
ret = cv2.imwrite(output_file, labeled_image)
if ret:
    print(f"Successfully saved {output_file}")
else:
    print(f"Something went wrong.  ret from imwrite: {ret}")
