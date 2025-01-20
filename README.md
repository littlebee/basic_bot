# basic_bot

A Python centric, basic robotics platform providing
- an ultra lightweight, websockets based pub/sub service
- hardware support for various motors, servos, sensors
- support for vision and in frame object detection
- a simple `bb_create` script for creating new projects

## Status
*** This is still a work in progress ***

### Updates

January 20th, 2025 - Basic working central_hub and web_server services merged.  Working on adding basic motor controller service similar to Scatbot.

## Getting Started
```shell
pip install git+https://github.com/littlebee/basic_bot.git@main
bb_create my_new_project_dir
```
The above commands will
 - install the basic_bot python libs and scripts like `bb_create`, `bb_start`, `bb_stop`
 - create a project directory named `my_new_robot_project` and cd to it
 - add files for the basic shell of a webapp
 - add test of webapp
 - add files for example service that just increments a counter
 - add test for example service
 - add start.sh, stop.sh, upload.sh scripts to my_new_robot_project/
 - add build.sh and test.sh scripts to my_new_robot_project/
 - run build.sh and test.sh scripts


## TODO add updated version of How It All Works from strongarm + scatbot

https://github.com/littlebee/strongarm/blob/main/README.md#how-it-all-works



