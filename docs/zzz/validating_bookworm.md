
I validated the setup_on_pi_bookworm.md by uploading [daphbot-due](https://github.com/littlebee/daphbot-due) to the Raspberry pi4 and pi5 (from my dev machine in the daphbot-due root project dir):
```sh
./upload.sh pi5.local
```

### Install daphbot-due dependencies

Install port audio (needed by sounddevice pip package)
```sh
sudo apt-get install portaudio19-dev
python -m pip install sounddevice
```

### Install Requirements

ssh into pi5.local and:
```sh
cd daphbot_due
python -m pip install -r requirements.txt
rm -Rf logs/*
```

### Start the daphbot services
```sh
./start.sh
```

wait a sec and then clear the termimal, cat the logs and look for errors:
```sh
clear
cat logs/*
```

## It all worked!  __with a USB camera__

If the `basic_bot.services.vision` successfully started, you can open
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
                "bounding_box": [
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

Note: the above was using a USB connected camera.