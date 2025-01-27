
First need to install build and test dependencies:
```sh
pip install -r requirements.txt
```

Install mypy types:
```sh
mypy --install-types
```


To build:
```sh
python -m build
```

To install as editable for dev testing without having to reinstall between changes:
```sh
pip install --editable .
```

Install the dependencies for testing


Run the main test.sh script from the project root dir:
```sh
./test.sh
```
...will run all of the tests in test/integration_tests and test/e2e_tests


## TIPS

### DEBUGGING TESTS

It is easier to start with an empty logs dir.  From the root of your project dir:
```sh
rm -Rf logs/*
```

You can make the test failure output more readable and narrow the tests to run a
single test using `pytest -vv` and `pytest -k` respectively.  For example:
```sh
pytest -vv tests/integration_tests/test_central_hub.py -k test_connect_identify
```

You can dump all logs to a screen and quickly look for errors.  It's easier to
read if only running one test. To figure out which service a specific line
was output to, scan up in the logs for identity
```sh
cat logs/*
```