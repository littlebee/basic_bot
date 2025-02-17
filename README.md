# basic_bot

A Python centric, basic robotics platform providing

- an ultra lightweight, websockets based pub/sub service
- hardware support for various motors, servos, sensors
- support for vision and in frame object detection
- a simple `bb_create` script for creating new projects

📖 [Official API Docs](https://littlebee.github.io/basic_bot/)
📚 [Github Repository](https://github.com/littlebee/basic_bot)
🎯 [Comments and suggestions welcomed](https://github.com/littlebee/basic_bot/issues)


## Status
*** This is still a work in progress ***

### Updates

20250128 - We have [online hosted docs](https://littlebee.github.io/basic_bot/)! 🎉

20250127 - It can see! Working basic_bot.services.vision_cv service that uses open cv2 and tensorflow lite.  Still trying to decide what else is needed in the beta version - support for GPIO in?  Doing this in parallel with implementing the first working example of using basic_bot - [daphbot-due](https://github.com/littlebee/daphbot-due)


20250120 - Basic working central_hub and web_server services merged.  Working on adding basic motor controller service similar to Scatbot.

## Getting Started
On your development computer (not your bot's onboard computer; see later in this doc)

```sh
# first create or activate a python venv
python -m venv my_new_project_venv
source my_new_project_venv/bin/activate

# installs the basic_bot package
python -m pip install git+https://github.com/littlebee/basic_bot.git@main

# creates a new robotics project
bb_create my_new_robot_project
```
The bb_create command above will

- add files for the basic shell of a webapp
- add test of webapp
- add files for example service that increments a counter
- add test for example service
- add start.sh, stop.sh, upload.sh scripts to my_new_robot_project/
- add build.sh and test.sh scripts to my_new_robot_project/
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
... which will start all services in the `` file.  Each service runs in as a process.

You can start a hot development web server that will show your changes to the webapp/ code in near real time most of the time :).
```sh
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
- `/home/pi/my_bot` is the optional directory you wish to upload to. If not specified, the default is `home/$USER/basic_bot`. The directory will be created if it does not already exist.

Notes:

I work on a macbook and use iTerm2 for terminal.  One of the additions I like to make to the standard setup, is to use the same user name on the Pi that I use locally on my mac.  This allows not having to type `ssh raspberry@mybot.local`, because the name is the same just `ssh mybot.local` works.

I also like to add my public key to the `~/.ssh/authorized_keys` file on the remote SBC. This will stop it from prompting you for the password on every SSH command (upload.sh uses rsync which uses ssh).   I made a [gist of the script](https://gist.github.com/littlebee/b285f0b9d219e56fe29b7248440309a5) I use to upload my public key to new boards.


## Run the software on your robot

First `ssh` into the onboard computer and `cd path/uploaded/to`.

### Create and source python venv

Unfortunately some things like Picamera2 require the shipped python libs
so be sure to include `--system-site-packages` below when running on
Raspberry Pi 4 or 5.

```sh
python -m venv --system-site-packages my_new_project_venv
source my_new_project_venv/bin/activate
```

### Upgrade pip

basic_bot package install requires a newer version of pip than ships with
Python 3.9 on Bullseye and possibly other Linux based OS.  Generally, it's
a good idea to get the latest `pip`
```sh
python -m pip install --upgrade pip
```


### Install basic_bot onboard

```sh
python -m pip install git+https://github.com/littlebee/basic_bot.git@main
```


### Add BB_ENV export

The onboard computer of the robot is considered the "production" environment.
Some basic_bot modules (like motor controllers) may load mock versions of
themselves when not running in the production environment. This is intended
to keep from accidentally, for example, running the bot off of your workbench
or your robotic arm smacking you in the face because you ran tests or diagnostics
on the onboard system.

The following command will add `BB_ENV=production` to the environment variables
for your OS user when running a bash shell:
```sh
echo "export BB_ENV=production" >> ~/.bashrc
source ~/.bashrc
```

You can also prefix env vars on the command line in most shells:
```sh
BB_ENV=production bb_start
```

If you plan on starting your robot software at boot using `/etc/rc.local`, just
add the export below to rc.local before starting your robot.
```sh
export BB_ENV=production

/path/to/scriptThatStartsMyBot.sh
```

## Start the onboard services

Then **`cd` the the directory** you uploaded to:
```sh
bb_start
```
will start all of the services in  `./basic_bot.yml` as individual processes running detached.  If your shell/terminal is closed, they will keep running.


## Debugging issues

You can debug issues with a service by looking at the ./logs/* files for each service.

basic_bot also provides several scripts in the `basic_bot.debug` package that can be used to diagnose 3rd party software like opencv and Tensor Flow Lite.

First stop all services:
```sh
bb_stop
```

To see if your opencv installation is working correctly with your robot's camera:
```sh
python -m python -m basic_bot.debug.test_opencv_capture
```

The above may fail because opencv capture doesn't work with libcamera (Pi4 and Pi5) yet.  Try this on Raspbery:
```sh
python -m python -m basic_bot.debug.test_picam2_opencv_capture
```

## Adding your own UI, too?

Ya sure, you betcha!  The created `my_new_robot_project/webapp` is just an example of how to interact with central_hub.  You can add your own content or completely replace it with say Next.js if that is your thing.

The created ./webapp is currently a Vite app, created with `yarn create vite`.   The `-m basic_bot.services.web_server` service currently is hard coded (TODO: fix) to look in ./webapp/dist for index.html and the rest is up to the app.

If you're want to use another frontend framework, you should be able to symbolic link where ever that framework's bundler puts it's build assets like index.html to `./webapp/dist`


## Build non Python services?

Sure, anything that you can run from a shell prompt, you can use as a service and `bb_start` and `bb_stop` will manage it in the background.   All you need is websockets and JSON parsing support in your language of choice and you can do it!

See [central_hub service docs](https://littlebee.github.io/basic_bot/Api%20Docs/services/central_hub/) for more information on the interface for subscribing and publishing state.


## Examples

[daphbot-due](https://github.com/littlebee/daphbot-due) (In progress) A robot for keeping your pet off of the kitchen counter.

[stongarm](https://github.com/littlebee/strong-arm) (TBD: need to back port it to using bb). A robotic arm application with visual simulation.

[svgarm]() (TBD: dream stage) A robotic arm that can be mounted above a whiteboard and draw svgs sent to it.


## Will it run on Windows?

Answer is IDK, yet.  Wherever possible, I've tried to use the cross-platform, pure Python, file system and os abstractions.

See also, https://github.com/littlebee/basic_bot/issues/61


## How it all works

Start with the docs for [[central_hub service docs](https://littlebee.github.io/basic_bot/Api%20Docs/services/central_hub/)]

### TODO add updated version of How It All Works from scatbot

!()[https://github.com/littlebee/scatbot/blob/c2800de8906b14173201d16030e8d390157eb641/docs/img/scatbot-systems-diagram.png]



