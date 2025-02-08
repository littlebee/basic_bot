import pytest


"""
Note that we are testing OUR commons/tflite_detect.py module,
not the tflite_runtime.  Only importing here to confirm
that it is installed. If it is not installed, we skip the test.

Try `python -m basic_bot.debug.test_tflite_runtime` for a test of
the tflite_runtime package itself.
"""

try:
    # first test to see if tflite_runtime is installed?
    # flake8 will complain about the import not benig used
    import tflite_runtime  # noqa: F401 # type: ignore
except ImportError:
    """
    tflite_runtime is hard to install on mac and even worse on Apple Silicon.

    It does run on Ubuntu Linux and runs on the Raspberry Pi.  The CI/CD
    GitHub Actions runner is Ubuntu Linux and you should see it running there.
    """
    print("tflite_runtime not installed. Skipping test")
    pytest.skip(
        "tflite_runtime not installed. Skipping test",
        allow_module_level=True,
    )
