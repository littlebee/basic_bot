# basic_bot

A Python centric, basic robotics platform providing

- an ultra lightweight, websockets based pub/sub service
- hardware support for various motors, servos, sensors
- support for vision and in frame object detection
- a simple `bb_create` script for creating new projects

See official [API Docs](https://littlebee.github.io/basic_bot/)

## Status
*** This is still a work in progress ***

### Updates

20250128 - We have [online hosted docs](https://littlebee.github.io/basic_bot/)! 🎉

20250127 - It can see! Working basic_bot.services.vision_cv service that uses open cv2 and tensorflow lite.  Still trying to decide what else is needed in the beta version - support for GPIO in?  Doing this in parallel with implementing the first working example of using basic_bot - [daphbot-due](https://github.com/littlebee/daphbot-due)


20250120 - Basic working central_hub and web_server services merged.  Working on adding basic motor controller service similar to Scatbot.

## Getting Started
On your development computer (not your bot's onboard computer; see later in this doc)

```sh
python3 -m pip install git+https://github.com/littlebee/basic_bot.git@main
bb_create my_new_project_dir
```
The above commands will

- install the basic_bot python libs and scripts like `bb_create`, `bb_start`, `bb_stop`
- create a project directory named `my_new_robot_project`
- add files for the basic shell of a webapp
- add test of webapp
- add files for example service that increments a counter
- add test for example service
- add start.sh, stop.sh, upload.sh scripts to my_new_project_dir/
- add build.sh and test.sh scripts to my_new_project_dir/
- run build.sh and test.sh scripts

After `bb_create` finishes you should be able to

```sh
cd my_new_robot_project
```

### Everything created is yours to edit

`bb_create` is single use per project and will not overwrite an existing directory.

The created app should run on any OS supported by Python >= 3.9 with a Posix compliant shell.  I've tested this assertion on macOS >= 14.7, on Raspberry PI 4 with Raspian Bullseye, and on the Raspberry Pi 5 w/ Debian Bookworm.  Additionally, the CI/CD test system for this project validates that everything works on `ubuntu-latest`.

Python >= 3.9 is required.  It's also a good idea to make sure `python` and `pip` commands are pointing to the correct version (3.9) if you are using a virtual environment like Anaconda or Miniconda.

To build and use the created `./webapp` example, you must have Node.js >= v20.18, and `npm` needs to be in your path.

From there, check out the .sh files in the root of my_new_robot_project.  Commands to build, start in the background, run integration tests for the Python example "worthless_counter" service, and run example integration test.

## Kicking the tires locally

You can start the services locally in the background (from your project root dir on dev machine):
```sh
./start.sh
```
... which will start all services in the `services.cfg` file.  Each service runs in as a process.

You can start a hot development web server that will show your changes to the webapp/ code in near real time most of the time :).
```
cd webapp
npm run dev
```

For more information about hacking on the code, running tests, and debugging, see [CONTRIBUTING.md](https://github.com/littlebee/basic_bot/blob/main/CONTRIBUTING.md).


## Upload to your robot

Also included is an example `upload.sh` script that can be used to upload your code to your robot's onboard computer.  The example `upload.sh` uses `rsync` and requires that both your local and onboard computer need to have SSH installed and properly set up.  If you can `ssh my_rad_robot.local` or by IP, you should be able to use rsync and the upload example.

Example:
```sh
./upload.sh pi@my_raspberry_bot.local /home/pi/my_bot
```

- `pi` above is the username
- `my_raspberry_bot.local` above is the hostname to upload can be replaced by IPAddress
- `/home/pi/my_bot` is the directory you wish to upload to.  The directory will be created if it does not already exist.

Notes:

I work on a macbook and use iTerm2 for terminal.  One of the additions I like to make to the standard setup, is to use the same user name on the Pi that I use locally on my mac.  This allows not having to type `ssh raspberry@mybot.local`, because the name is the same just `ssh mybot.local` works.

I also like to add my public key to the `~/.ssh/authorized_keys` file on the remote SBC. This will stop it from prompting you for the password on every SSH command (upload.sh uses rsync which uses ssh).   I made a [gist of the script](https://gist.github.com/littlebee/b285f0b9d219e56fe29b7248440309a5) I use to upload my public key to new boards.


## Run the software on your robot

First `ssh` into the onboard computer and `cd path/uploaded/to`.

Before running for the first time, in an ssh shell, install the basic_bot package:
```
python3 -m pip install git+https://github.com/littlebee/basic_bot.git@main
```

Then from within the the directory you uploaded to:
```
./start.sh
```
will start all of the services in  `./services.cfg` as individual processes running detached.  If your shell/terminal is closed, they will keep running.

You can debug issues with a service by looking at the ./logs/* files for each service.

## Adding your own UI, too?

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



