
# basic_bot.debug

This package is a collection of individual test programs meant to validate the correct setup and installation of 3rd party packages like opencv and tensorflow.

You can run them using the -m switch to python from the command line on either your workstation or your robot's on board computer.  Ex:

```sh
# tests that opencv is working and outputs an "opencv_test_output.jpg"
python -m basic_bot.debug.test_opencv_img
```