import os
import json
import time
from typing import Dict, Any, List, Optional

import basic_bot.commons.log as log
import basic_bot.commons.constants as c

PERSISTED_STATE_FILE = "./persisted_state.json"
TEST_PERSISTED_STATE_INPUT_FILE = "./tests/persisted_state.json"
TEST_PERSISTED_STATE_OUTPUT_FILE = "./tests/persisted_state_out.json"


class HubState:
    def __init__(
        self, default_state: Dict[str, Any] = {}, persisted_state_keys: List[str] = []
    ) -> None:
        self.state: Dict[str, Any] = {}
        self.state.update(default_state)
        log.info(f"hub_state initialized with {self.state}")
        self.persisted_state_keys = persisted_state_keys
        self.init_persisted_state()

    def get(self, keys_requested: List[str]) -> str:
        requested_state = None
        if keys_requested:
            requested_state = {
                key: self.state[key] for key in keys_requested if key in self.state
            }
        else:
            requested_state = self.state
        return requested_state

    def update_state_from_message_data(self, message_data: Dict[str, Any]) -> None:
        """Update state from received message data."""
        for key, data in message_data.items():
            self.state[key] = data
            self.state[f"{key}_updated_at"] = time.time()

    def persist_state(self) -> None:
        """Persist the current state to a file."""

        if c.BB_ENV == "test" or self.persisted_state_keys == []:
            # allow tests to have and alter a persisted state file
            # for initialization, but we don't ever want to write to it.
            # Otherwise, later test modules would initialize with the
            # altered state.
            return

        try:
            with open(PERSISTED_STATE_FILE, "w") as f:
                json.dump(self.serialize_state(), f)
        except IOError as e:
            log.error(f"Failed to persist state: {e}")

    def serialize_state(self, keys_requested: Optional[List[str]] = None) -> str:
        """Serialize the current state to JSON."""

        keys_requested = keys_requested or self.state.keys()
        requested_state = self.state
        if keys_requested:
            requested_state = {
                key: self.state[key] for key in keys_requested if key in self.state
            }

        try:
            return json.dumps({"type": "state", "data": requested_state})
        except json.JSONDecodeError as e:
            log.error(f"Failed to serialize state: {e}")
            return json.dumps({"type": "state", "data": {}})

    def init_persisted_state(self) -> None:
        """Initialize the state from the persisted state file."""

        file = PERSISTED_STATE_FILE
        if c.BB_ENV == "test":
            log.info(
                f"Running in test mode, using {TEST_PERSISTED_STATE_INPUT_FILE} persisted state file"
            )
            file = TEST_PERSISTED_STATE_INPUT_FILE

        try:
            # if the file exists, load it
            if os.path.exists(file):
                with open(file, "r") as f:
                    persisted_state = json.load(f)
                    for key in self.persisted_state_keys:
                        if key in persisted_state:
                            self.state[key] = persisted_state[key]
        except (IOError, json.JSONDecodeError) as e:
            log.error(f"Failed to initialize persisted state: {e}")
