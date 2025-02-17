#!/usr/bin/env python3
"""
This diagnostic script will test the installation of picamera2, and its ability to
capture a 10sec video from a camera and save it to a file. Using cv2 to save the video.

usage:
```sh
python -m basic_bot.debug.test_picam2_opencv_capture
```
"""
import os
import time

from picamera2 import Picamera2  # type: ignore
from libcamera import controls  # type: ignore
import cv2

DURATION = 10


size = (640, 480)
video_file = os.path.join(os.getcwd(), "picamera2_capture_test_output.mp4")


# Create an object to read
# from camera
camera = Picamera2()
camera.configure(
    camera.create_video_configuration(main={"format": "RGB888", "size": size})
)
camera.start()

# Set the camera to continuous autofocus
try:
    # on PI4 bullseye with Raspberry Camera Module 2, this fails with:
    # RuntimeError: Control AfMode is not advertised by libcamera
    camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
except:
    print("Failed to set autofocus mode to continuous.  This is not fatal.")

print(f"recording {DURATION} secs of video...")
start = time.time()
num_frames = 0
captured_frames = []
while time.time() - start <= DURATION:
    frame = camera.capture_array("main")

    if frame is not None:
        captured_frames.append(frame)
        num_frames += 1
    else:
        print(f"ERROR: Failed to capture frame {num_frames}.")
        exit(1)

duration = time.time() - start
capture_fps = num_frames / duration
print(f"recorded {num_frames} frames in {duration}s ({capture_fps:.2f} fps)")

print(f"\nSaving video to {video_file}")
start = time.time()
writer = cv2.VideoWriter(
    video_file,
    cv2.VideoWriter_fourcc(*"mp4v"),  # type: ignore
    capture_fps,
    size,
)
for frame in captured_frames:
    writer.write(frame)

duration = time.time() - start
print(f"saved {num_frames} frames in {duration}s ({num_frames/duration:.2f} fps)")


# When everything is done, release
# the video capture and video
# write objects
writer.release()


print(f"The video was successfully saved as {video_file}")
