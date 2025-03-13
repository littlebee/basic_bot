#!/usr/bin/env python

import cv2
import sys

# Argv can be any video file path or URL accepted by OpenCV

data = cv2.VideoCapture(sys.argv[1])

# count the number of frames
frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
fps = data.get(cv2.CAP_PROP_FPS)

# calculate duration of the video
seconds = frames / fps
print(f"duration in seconds: {seconds}")
