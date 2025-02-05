The goals for this project are:
1. provide significantly simpler alternative to ROS
1. run stand-alone; decentralized
1. install and run on small SBCs like raspberry pi
1. distribute a pip package
1. maybe distribute a npm package for the typescript web components
1. simplify getting started on new projects.  This would ideally be something like:
```
pip3 install basic_bot
python3 basic_bot:create my_new_robot_project
```
which would
 -
 - create a project directory (`mkdir my_new_robot_project`) with start, stop, upload scripts;
 - cd to that directory
 - create .gitignore file from basic python template with additions for logs/ pids/ etc.
 - create logs/ directory
 - create pids/ directory
 - create src/ directory
 - create webapp/ directory and populate it with a basic vite starter project in Typescript

Much of the design originally will come from https://github.com/littlebee/strongarm and strip it down to just the parts that are used for all bots like central-hub, with optional submodules for things like Raspberry Pi system stats, servo control, motor control, vision, and image object recognition.

My intent is to later update strongarm to use this package instead of it's own versions of some of these subsystems.

