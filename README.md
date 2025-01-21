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

 After `bb_create` finishes you should be able to
 ```shell
 cd my_new_robot_project
 ```

### Everything created is yours to edit

`bb_create` is single use per project and will not overwrite existing directory.

The created app should run on any OS supported by Python >= 3.9 with a Posix compliant shell.  I've tested this assertion on macOS >= 14.7 and on Raspberry PI 4 with Raspian Bullseye.

To build and use the created `./webapp` example, you will need to have Node.js >= v20.18 and `npm` needs to be in your path.

From there, check out the .sh files in the root of my_new_robot_project.  Commands to build, start in the background, run integration tests for the Python example "worthless_counter" service, and run example integration test.

Also included is an example `upload.sh` script that can be used to upload your code to your robot's onboard computer.  The example `upload.sh` uses `rsync` and requires that both your local and onboard computer need to have SSH installed and properly set up.  If you can `ssh my_rad_robot.local` or by IP, you should be able to use rsync and the upload example.

### Adding your own UI, too?

Ya sure, you betcha!  The created `my_new_robot_project/webapp` is just an example of how to interact with central_hub.  You can add your own content or completely replace it with say Next.js if that is your thing.

The created ./webapp is currently a Vite app, created with `yarn create vite`.   The `-m basic_bot.services.web_server` service currently is hard coded (TODO: fix) to look in ./webapp/dist for index.html and the rest is up to the app.

If you're want to use another frontend framework, you should be able to symbolic link where ever that framework's bundler puts it's build assets like index.html to `./webapp/dist`

### Will it run on Windows?

 Answer is IDK, yet.  Wherever possible, I've tried to use the cross-platform pure Python file system abstraction.  If you look at the `start.sh` and `stop.sh` scripts in the root of the created project, you will see that those just call scripts which `pip3 install ` or `conda install `, via SetupTools should have installed globally assuming pip3 is in your environment.

 So maybe `./start.sh` does nothing on Windows, but `bb_start` will?  Add a .bat file; maybe just rename *.sh -> *.bat?   [Waves arms; not a windows user for years]


#### TODO: add links to other bots using their own components as examples (like strongarm)



## How it all works


### TODO add updated version of How It All Works from strongarm + scatbot

https://github.com/littlebee/strongarm/blob/main/README.md#how-it-all-works



