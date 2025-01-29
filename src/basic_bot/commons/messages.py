"""
Functions from this module are used to send messages to the central_hub
via websockets.
"""

import json
from enum import Enum
from typing import Optional, List, Dict, Any, Union, Literal

from basic_bot.commons import log, constants as c


class MessageType(Enum):
    """Message types for communication to/from central_hub."""

    STATE_UPDATE = "stateUpdate"
    STATE = "state"
    IDENTITY = "iseeu"


async def send_message(websocket: Any, message: Dict[str, Any]) -> None:
    """Send a message in the form of a dictionary to central_hub."""
    json_message = json.dumps(message)
    if c.BB_LOG_ALL_MESSAGES:
        log.info(f"sent {json_message} to {websocket.remote_address[1]}")
    await websocket.send(json_message)


async def send_identity(websocket: Any, name: str) -> None:
    """
    Send the `identity` type message to central_hub.  Name should uniquely
    identify the service.
    """
    await send_message(
        websocket,
        {
            "type": "identity",
            "data": name,
        },
    )


async def send_subscribe(
    websocket: Any, subscriptionNames: Union[List[str], Literal["*"]]
) -> None:
    """
    Send the `subscribeState` message type to central_hub.

    `subscriptionNames` should be an array of keys to subscribe or "*"
    to subscribe to all keys.
    """
    await send_message(
        websocket,
        {
            "type": "subscribeState",
            "data": subscriptionNames,
        },
    )


async def send_get_state(websocket: Any, keys: Optional[List[str]] = []) -> None:
    """
    Send the `getState` message type to central_hub optionally specifying a list
    of keys to get the state.
    """
    await send_message(
        websocket,
        {
            "type": "getState",
            "data": keys,
        },
    )


async def send_update_state(websocket: Any, stateData: Dict[str, Any]) -> None:
    """
    Send the `updateState` message type to central_hub with the key->value state data to update.
    """
    await send_message(
        websocket,
        {
            "type": "updateState",
            "data": stateData,
        },
    )
