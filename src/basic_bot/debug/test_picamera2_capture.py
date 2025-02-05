#!/usr/bin/env python3
"""
This diagnostic script will test the installation of picamera2, and its ability to
capture a 10sec video from a camera and save it to a file. Using cv2 to save the video.

usage:
```sh
python -m src.basic_bot.debug.test_picamera2_capture [video_channel]
```
"""
import os
import sys
import time

from picamera2 import Picamera2  # type: ignore
import cv2

DURATION = 10

video_channel = 0
if len(sys.argv) > 1:
    video_channel = int(sys.argv[1])

size = (1280, 720)
video_file = os.path.join(os.getcwd(), "picamera2_capture_test_output.mp4")


# Create an object to read
# from camera
camera = Picamera2()
camera.start()

# print(
#     f"starting video_channel={video_channel} size={size} capture_fps={capture_fps}",
# )

print(f"recording {DURATION} secs of video...")
start = time.time()
num_frames = 0
captured_frames = []
while True:
    frame = camera.capture_array()

    if frame is not None:
        # Write the frame into the
        # file 'filename.avi'
        # writer.write(frame)
        captured_frames.append(frame)
        num_frames += 1
    else:
        print(f"ERROR: Failed to capture frame {num_frames}.")
        exit(1)

    # runs for 30s
    if time.time() - start >= DURATION:
        break

duration = time.time() - start
print(f"recorded {num_frames} frames in {duration}s ({num_frames/duration:.2f} fps)")

print(f"\nSaving video to {video_file}")
# Below VideoWriter object will create
# a frame of above defined The output
# is stored in 'filename.avi' file.
start = time.time()

writer = cv2.VideoWriter(
    video_file,
    cv2.VideoWriter_fourcc(*"mp4v"),  # type: ignore
    30,
    size,
)
for frame in captured_frames:
    writer.write(frame)

duration = time.time() - start
print(f"saved {num_frames} frames in {duration}s ({num_frames/duration:.2f} fps)")


# When everything done, release
# the video capture and video
# write objects
writer.release()


print(f"The video was successfully saved as {video_file}")
