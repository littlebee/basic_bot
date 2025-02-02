#!/bin/sh


# install all of the apt dependencies
sudo apt install -y python3-kms++ libcap-dev libcamera-dev python3-libcamera python3-picamera2

# install the python dependencies
python -m pip install -y rpi-libcamera picamera2

