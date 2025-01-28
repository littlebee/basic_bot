import json
import time
from typing import Dict, Any, List, Optional

import basic_bot.commons.log as log


class HubState:
    """
    This class manages the local state of the hub.  It is initialized with a default
    initial state and can be updated with new state data.

    """

    def __init__(self, default_state: Dict[str, Any] = {}) -> None:
        """
        Initializes the hub state with the default state.
        """
        self.state: Dict[str, Any] = {}
        self.state.update(default_state)
        log.info(f"hub_state initialized with {self.state}")

    def get(self, keys_requested: List[str]) -> Dict[str, Any]:
        """Return the requested state data for a list of state keys."""
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

    def serialize_state(self, keys_requested: Optional[List[str]] = None) -> str:
        """Serialize the current state to JSON."""

        keys_requested = keys_requested or list(self.state.keys())
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
