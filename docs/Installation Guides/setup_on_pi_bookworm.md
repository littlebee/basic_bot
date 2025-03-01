
# Setup basic_bot on a Raspberry Pi4 or Pi5 with Debian Bookworm

...for basic_bot, ovencv and tflite

## Flash and Boot

First you need to flash an image to a microcard reader using the [Raspberry Pi installer](https://www.raspberrypi.com/software/).

Debian Bookworm is the new Raspian Bullseye.  [Good article](https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/) on the differences. The rest of this guide is specific to Bookwork, which at the time of this update is the default OS used by the Raspberry Pi Imager.


Here is a montage of the various settings I chose:

![](images/pi5-setup/pi5%20setup%20screen%201.jpg){: style="transform:scale(.8);"}
![](images/pi5-setup/pi5%20setup%20screen%202.jpg){: style="transform:scale(.8);"}
![](images/pi5-setup/pi5%20setup%20screen%203.jpg){: style="transform:scale(.8);"}
![](images/pi5-setup/pi5%20setup%20screen%204.jpg){: style="transform:scale(.8);"}

__Just answer yes to the remaining questions and ...__

![](images/pi5-setup/goodtogo.jpg){: style="transform:scale(.7);"}}

## SSH into the pi

```sh
ssh pi5.local
```

Verify that Debian Bookwork was installed:
```sh
bee@pi5:~ $ cat /etc/os-release
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```


## Update and upgrade OS


```sh
sudo apt update
sudo apt full-upgrade
sudo reboot
```
SSH back into Raspberry Pi after reboot.

Check versions:
```sh
bee@pi5:~ $ python --version
Python 3.11.2
bee@pi5:~ $ python -m pip --version
pip 23.0.1 from /usr/lib/python3/dist-packages/pip (python 3.11)
```

## Install Basic Bot

Follow the [instructions in Getting Started](https://littlebee.github.io/basic_bot/#run-the-software-on-your-robot) for installing and
running basic_bot.


## Use picamera2 instead of opencv if using ribbon cable camera

As of Feb 7, 2025, OpenCV camera capture [will NOT work on Debian Bullseye or Bookworm
with a ribbon cable camera](https://github.com/opencv/opencv/issues/21653).

You must either use a USB camera or use the `basic_bot.commons.camera_picamera`
module.

See the [API docs for using camera_picamera](https://littlebee.github.io/basic_bot/Api%20Docs/commons/camera_picamera/) for more information about how to use.