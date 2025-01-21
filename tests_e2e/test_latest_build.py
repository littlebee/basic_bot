"""
This pytest test opens the ../dist/basic_bot-0.1.0.tar.gz file and
asserts the following:

- The file exists

- The uncompressed file has the following files or directories:
    src/basic_bot/__init__.py
    src/basic_bot/create.py
    src/basic_bot/created_files
    src/basic_bot/created_files/webapp

- The uncompressed file does not contain anyof  the following files or
directories recursively:
    __pycache__
    node_modules
    package-lock.json

"""

import tarfile
from pathlib import Path

DIST_FILE = Path("./dist/basic_bot-0.1.0.tar.gz")
REQUIRED_FILES = [
    "src/basic_bot/__init__.py",
    "src/basic_bot/create.py",
    "src/basic_bot/created_files",
    "src/basic_bot/created_files/webapp",
]
EXCLUDED_PATTERNS = ["__pycache__", "node_modules", "package-lock.json"]


def test_dist_file_exists():
    assert DIST_FILE.exists(), f"Distribution file {DIST_FILE} not found"


def test_required_files_exist():
    with tarfile.open(DIST_FILE, "r:gz") as tar:
        members = tar.getnames()
        for required_file in REQUIRED_FILES:
            matching = [m for m in members if required_file in m]
            assert matching, f"Required file/directory not found: {required_file}"


def test_excluded_files_not_present():
    with tarfile.open(DIST_FILE, "r:gz") as tar:
        members = tar.getnames()
        for excluded in EXCLUDED_PATTERNS:
            matching = [m for m in members if excluded in m]
            assert not matching, f"Excluded pattern found: {excluded} in {matching}"
