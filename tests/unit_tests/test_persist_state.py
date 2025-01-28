"""
    This is a unit test of basic_bot.commons.persist_state.PersistState.

    I added this unit test because it was currently not used anywhere else
    in basic_bot package.  The functionality was once part of hub_state and
    will be used in the future when we port the strongarm and specifically
    the arm_configs_provider service.
"""

import os
import json

from basic_bot.commons.hub_state import HubState
from basic_bot.commons.persist_state import PersistState

TEST_FILE = "./test_persist_state.json"

INITIAL_STATE = {
    "test_str": "test_value",
    "test_object_1": {"test_bool": False},
    "test_object_2": {"test_bool": False},
}

UPDATED_STATE = {
    "test_object_2": {"test_bool": True},
}


def remove_file_if(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def teardown_module():
    remove_file_if(TEST_FILE)


def test_init_with_file():
    hub_state = HubState({})
    with open(TEST_FILE, "w") as f:
        f.write(json.dumps(INITIAL_STATE))

    PersistState(hub_state, TEST_FILE, ["test_object_1", "test_object_2"])

    assert os.path.exists(TEST_FILE), "File should still exist"
    assert hub_state.state == {
        "test_object_1": {"test_bool": False},
        "test_object_2": {"test_bool": False},
    }, "State should have been updated with just the persisted keys data"


def test_init_with_defaults():
    hub_state = HubState(INITIAL_STATE)
    with open(TEST_FILE, "w") as f:
        f.write(json.dumps(UPDATED_STATE))

    PersistState(hub_state, TEST_FILE, ["test_object_1", "test_object_2"])

    assert os.path.exists(TEST_FILE), "File should still exist"
    assert hub_state.state == {
        "test_str": "test_value",
        "test_object_1": {"test_bool": False},
        "test_object_2": {"test_bool": True},
    }, "State should have been updated"


def test_init_without_file():
    hub_state = HubState({})

    remove_file_if(TEST_FILE)

    PersistState(hub_state, TEST_FILE, ["test_object_1", "test_object_2"])

    assert not os.path.exists(TEST_FILE), "File should not have been created"
    assert hub_state.state == {}, "State should still be empty"
