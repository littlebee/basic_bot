#!/usr/bin/python3
"""
This diagnostic script will test the installation of picamera2, and its ability to
capture a 10sec video from a camera and save it to a file. Using ffmpeg to save the video.

usage:
```sh
python -m basic_bot.debug.test_picam2_ffmpeg_capture 0
```

Sourced from:
https://github.com/raspberrypi/picamera2/blob/main/examples/mp4_capture.py
"""
import os
import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

video_file = os.path.join(os.getcwd(), "picam2_ffmpeg_test_output.mp4")

picam2 = Picamera2()
video_config = picam2.create_video_configuration()
picam2.configure(video_config)

encoder = H264Encoder(10000000)
output = FfmpegOutput("picam2_ffmpeg_test_output.mp4")

print("Recording 10 seconds of video...")
picam2.start_recording(encoder, output)
time.sleep(10)
picam2.stop_recording()

print(f"Done: Video saved to {video_file}")
