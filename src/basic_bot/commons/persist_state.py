import os
import json
from typing import List

from basic_bot.commons import log, constants as c
from basic_bot.commons.hub_state import HubState


class PersistState:
    """Class to handle persisting the bot state to a file."""

    def __init__(
        self, hub_state: HubState, file_path: str, persisted_state_keys: List[str]
    ) -> None:
        self.hub_state = hub_state
        self.persisted_state_keys = persisted_state_keys
        self.file_path = file_path

        self._init_persisted_state()

    def persist_state(self) -> None:
        """Persist the current state to a file."""

        try:
            with open(self.file_path, "w") as f:
                f.write(self.hub_state.serialize_state(self.persisted_state_keys))
        except IOError as e:
            log.error(f"Failed to persist state: {e}")

    def _init_persisted_state(self) -> None:
        """Initialize the persisted state from a file."""
        log.info(
            f"basic_bot.commons.persist_state: initializing persisted state from {self.file_path}"
        )

        try:
            # if the file exists, load it
            if not os.path.exists(self.file_path):
                log.info(
                    f"basic_bot.commons.persist_state: {self.file_path} does not exist"
                )
                return

            with open(self.file_path, "r") as f:
                persisted_state = json.load(f)
                for key in self.persisted_state_keys:
                    if key in persisted_state:
                        self.hub_state.state[key] = persisted_state[key]
        except (IOError, json.JSONDecodeError) as e:
            log.error(f"Failed to initialize persisted state: {e}")
