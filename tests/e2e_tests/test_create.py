import os
import tempfile
import shutil
import subprocess
import pytest

"""
This is an E2E test for the bb_create script.

It assumes that basic_bot has been `pip install`d local to where it is
running.  It will run the `bb_create` command from the local temp
directory and then test that the created project is in a good state.

use `pytest tests_e2e/test_create.py` to run this test.

This test may take a minute or to run as it is creating a new project
and running its build and test scripts.
"""


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    tmp_dir = tempfile.mkdtemp()
    old_dir = os.getcwd()
    os.chdir(tmp_dir)
    yield tmp_dir
    os.chdir(old_dir)
    shutil.rmtree(tmp_dir)


def test_create_project(temp_dir):
    """Test creating a new project"""
    project_name = "test_bot"

    # Run bb_create command
    result = subprocess.run(["bb_create", project_name], capture_output=True, text=True)
    print(f"test_create_project: output from bb_create {result}")
    assert result.returncode == 0

    # Check if project directory was created
    project_dir = os.path.join(temp_dir, project_name)
    assert os.path.exists(project_dir)

    # Check for essential files
    assert os.path.exists(os.path.join(project_dir, "README.md"))
    assert os.path.exists(os.path.join(project_dir, ".gitignore"))
    assert os.path.exists(os.path.join(project_dir, "build.sh"))
    assert os.path.exists(os.path.join(project_dir, "test.sh"))

    # Check webapp directory
    webapp_dir = os.path.join(project_dir, "webapp")
    assert os.path.exists(webapp_dir)
    assert os.path.exists(os.path.join(webapp_dir, "package.json"))

    # check if the webapp was built
    assert os.path.exists(
        os.path.join(webapp_dir, "node_modules")
    ), "This will fail if node/npm is not installed locally."
    assert os.path.exists(os.path.join(webapp_dir, "dist", "index.html"))

    # ensure there are no stranded pid files, by checking that the pids
    # directory contains no .pid files
    def is_pid_file(file):
        return file.endswith(".pid")

    pid_files = list(filter(is_pid_file, os.listdir(os.path.join(project_dir, "pids"))))
    print("pid_files", pid_files)

    assert not pid_files

    # ensure that none of the log/* files contain the string "Traceback"
    for log_file in os.listdir(os.path.join(project_dir, "logs")):
        if log_file == "vision.log":
            # until we have a better way to handle tflite_runtime not being
            # able to install on all platforms, we will skip this check
            continue

        file_path = os.path.join(project_dir, "logs", log_file)
        print(f"checking {file_path} log file for Traceback")
        with open(file_path, "r") as f:
            assert "Traceback" not in f.read()


def test_create_existing_project(temp_dir):
    """Test attempting to create project in existing directory"""
    project_name = "test_bot"

    # Create the directory first
    os.makedirs(os.path.join(temp_dir, project_name))

    # Try to create project
    result = subprocess.run(["bb_create", project_name], capture_output=True, text=True)
    assert "already exists" in result.stdout


def test_create_invalid_args():
    """Test bb_create with invalid arguments"""
    result = subprocess.run(["bb_create"], capture_output=True, text=True)
    assert result.returncode == 1
    assert "usage:" in result.stdout
