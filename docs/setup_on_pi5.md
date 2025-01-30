
# How to setup a Raspberry Pi5

...for basic_bot, ovencv and Adafruit Braincraft Hat

## Flash and Boot

First you need to flash an image to a microcard reader using the [Raspberry Pi installer](https://www.raspberrypi.com/software/).

Here is a montage of the various settings I chose:

![](images/pi5-setup/pi5%20setup%20screen%201.jpg){: style="transform:scale(.8);"}
![](images/pi5-setup/pi5%20setup%20screen%202.jpg){: style="transform:scale(.8);"}
![](images/pi5-setup/pi5%20setup%20screen%203.jpg){: style="transform:scale(.8);"}
![](images/pi5-setup/pi5%20setup%20screen%204.jpg){: style="transform:scale(.8);"}

__Just answer yes to the remaining questions and ...__

![](images/pi5-setup/goodtogo.jpg){: style="transform:scale(.7);"}}

## SSH into the pi5

Not sure why, but I didn't see the pi5 on my network by name `pi5.local`.  I had to initially connect via it's IP address and then run `sudo raspi-config` and change the hostname in there to "pi5.local".  Reboot and then it worked via name and you should be able to just `ssh pi5.local`.

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

Looks like Debian Bookworm is the new Raspian Bullseye.  [Good article](https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/) on the differences.

```sh
bee@pi5:~ $ python --version
Python 3.11.2
bee@pi5:~ $ python -m pip --version
pip 23.0.1 from /usr/lib/python3/dist-packages/pip (python 3.11)
```

💥 outa da box!  I think that will work.  Let's see what happens after apt upgrade.

```sh
sudo apt update
sudo apt full-upgrade
sudo reboot
```

## Max `tflight-support` version on Bookworm is 0.1.1a

Basic bot vision needs tflight-support >= v0.4.0 but Bookwork and Python 3.11.   [This issue on tensorflow's GH](https://github.com/tensorflow/tensorflow/issues/64365#issuecomment-2425043238) suggests that using Python 3.9 will allow you to install tflite-support==0.4.0.

So first install anaconda (miniforge) (makes switching and running multiple Python versions easier):
```sh
wget https://github.com/conda-forge/miniforge/releases/latest/download/miniforge3-linux-aarch64.sh
chmod +x miniforge3-linux-aarch64.sh

# note do not use sudo here
./miniforge3-linux-aarch64.sh
```
...agree to the license and accept the default location (/home/me/miniforge3)

Create and activate a new conda env based on python 3.9.2:
```sh
conda create -n basic_bot python==3.9.2
conda activate basic_bot
```

## Install port audio (needed by sounddevice pip package)
```
sudo apt-get install portaudio19-dev
python3 -m pip install sounddevice
```

## Install basic_bot and dependencies
```sh
python3 -m pip install git+https://github.com/littlebee/basic_bot.git@main
```

## Validate
Tested by uploading [daphbot-due](https://github.com/littlebee/daphbot-due) to the pi5 (from my dev machine in the daphbot-due root project dir):
```sh
./upload.sh pi5.local
```

Then on the pi5:
```sh
cd daphbot_due
pip install -r requirements.txt
rm -Rf logs/*
./start.sh
```

wait a sec and then clear the termimal, cat the logs and look for errors:
```sh
clear
cat logs/*
```

## It all works!

If the `basic_bot.services.vision_cv2` successfully started, you can open
a browser and see the video capture and recognition stats at (http://pi5.local:5801/stats).

I'm seeing some impressive stats!  Recognition is running at nearly 100% of the capture FPS at 24.79 frames per second.  Below are the stats:
```json
{
    "capture": {
        "totalFramesRead": 5938,
        "totalTime": 240.3178722858429,
        "overallFps": 24.70894046921789,
        "fpsStartedAt": 1738212599.538883,
        "floatingFps": 24.796676477203466
    },
    "recognition": {
        "last_objects_seen": [
            {
                "boundingBox": [
                    16,
                    8,
                    624,
                    456
                ],
                "classification": "person",
                "confidence": 0.515625
            },
        ],
        "fps": {
            "totalFramesRead": 5938,
            "totalTime": 240.08938884735107,
            "overallFps": 24.73245497648954,
            "fpsStartedAt": 1738212599.7694898,
            "floatingFps": 24.79684199179873
        },
        "total_objects_detected": 17774,
        "last_frame_duration": 0.030208587646484375
    }
}
```