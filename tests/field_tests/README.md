
This folder is for pytest tests that can only be run on the hardware
or has other dependencies.

These tests are generally not able to run on your dev OS or from CI/CD.

**VERY IMPORTANT:** If the service needs to be up and running, it should
be started before or currently be running. **BB_ENV=test should not be
used** and motors, cameras etc. should be allowed to be fully functional.