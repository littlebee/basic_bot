
# Contributing to basic_bot

Thank you, in advance, for your pull requests!


## Prereq

Make sure your `python` is Python 3.9 or later:
```sh
python --version
```

Install build and test dependencies:
```sh
python -m pip install -r requirements.txt
```

Install mypy types:
```sh
python -m mypy --install-types
```


## Building

To build use the build.sh script:
```sh
./build.sh
```

## Installing locally

To install build wheel (also calls ./build.sh)
```sh
./install.sh
```

To install as editable for dev testing without having to reinstall between changes:
```sh
./install-dev.sh
```

## Building and deploying docs

To build the docs from source code:
```sh
./build-docs.py
```
NOTE: the files generated by the above script, are in .gitignore

After running the build-docs.py script, you can verify that the docs look correct by starting the mkdocs server:
```sh
mkdocs serve
```
...and browsing to the url shown in the console (http://127.0.0.1:8000/)

### To deploy to GitHub Pages
```sh
./deploy-docs.sh
```

## Testing

Run the main test.sh script from the project root dir:
```sh
./test.sh
```
...will run all of the tests in test/integration_tests and test/e2e_tests


## Tips

### Debugging Docs Generation

#### Cheat Sheet

https://yakworks.github.io/docmark/cheat-sheet/

#### Bullet / Numbered list not rendering as list

- need a blank line before the dash or asterisk

### Debugging Tests

It is easier to start with an empty logs dir.  From the root of your project dir:
```sh
rm -Rf logs/*
```

You can make the test failure output more readable and narrow the tests to run a
single test using `pytest -vv` and `pytest -k` respectively.  For example:
```sh
pytest -vv tests/integration_tests/test_central_hub.py -k test_connect_identify
```

The `-s` argument to `pytest` can be used to see prints to stdout from the test file as it runs instead of only on fail.


You can dump all logs to a screen and quickly look for errors.  It's easier to
read if only running one test. To figure out which service a specific line
was output to, scan up in the logs for identity
```sh
cat logs/*
```

### Debugging CI/CD Test

Click into the details of the CICD run.  Look for the "Run Tests"
task and open it. Scroll to the bottom of the test output to find the failing test.

Sometimes it may not be obvious what failed from the test output.  Below the "Run Tests" step is the "Upload log artifacts" step.  Open it and you should see a link at the bottom labled "Artifact download URL:"  Click on it to download.  Unzip and inspect logs.