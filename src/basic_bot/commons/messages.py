"""
Functions from this module are used to send messages to the central_hub
via websockets.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any, Union, Literal, Protocol, runtime_checkable

from basic_bot.commons import log, constants as c


class MessageTypeIn(Enum):
    """Incoming message types (client → central_hub)."""
    IDENTITY = "identity"
    SUBSCRIBE_STATE = "subscribeState"
    GET_STATE = "getState"
    UPDATE_STATE = "updateState"
    PING = "ping"


class MessageTypeOut(Enum):
    """Outgoing message types (central_hub → client)."""
    STATE_UPDATE = "stateUpdate"
    STATE = "state"
    IDENTITY_ACK = "iseeu"
    PONG = "pong"


# Legacy enum for backward compatibility
class MessageType(Enum):
    """Message types for communication to/from central_hub."""
    STATE_UPDATE = "stateUpdate"
    STATE = "state"
    IDENTITY = "iseeu"


@runtime_checkable
class WebSocketProtocol(Protocol):
    """Protocol for websocket objects."""
    remote_address: tuple[str, int]

    async def send(self, data: str) -> None:
        ...


@dataclass
class BaseMessage:
    """Base message structure for websocket communication."""
    type: str
    data: Any = None


@dataclass
class IdentityMessage(BaseMessage):
    """Identity message for service registration."""
    type: str = MessageTypeIn.IDENTITY.value
    data: str = ""


@dataclass
class StateUpdateMessage(BaseMessage):
    """State update message for publishing state changes."""
    type: str = MessageTypeIn.UPDATE_STATE.value
    data: Optional[Dict[str, Any]] = None


@dataclass
class SubscribeMessage(BaseMessage):
    """Subscribe message for state key subscriptions."""
    type: str = MessageTypeIn.SUBSCRIBE_STATE.value
    data: Optional[Union[List[str], Literal["*"]]] = None


@dataclass
class GetStateMessage(BaseMessage):
    """Get state message for requesting current state."""
    type: str = MessageTypeIn.GET_STATE.value
    data: Optional[List[str]] = None


async def send_message(websocket: Any, message: Union[BaseMessage, Dict[str, Any]]) -> None:
    """Send a message to central_hub."""
    if isinstance(message, BaseMessage):
        message_dict = {"type": message.type, "data": message.data}
    else:
        message_dict = message

    json_message = json.dumps(message_dict)
    if c.BB_LOG_ALL_MESSAGES:
        log.info(f"sent {json_message} to {websocket.remote_address[1]}")
    await websocket.send(json_message)


async def send_identity(websocket: Any, name: str) -> None:
    """
    Send the `identity` type message to central_hub.  Name should uniquely
    identify the service.
    """
    message = IdentityMessage(data=name)
    await send_message(websocket, message)


async def send_subscribe(
    websocket: Any, subscriptionNames: Union[List[str], Literal["*"]]
) -> None:
    """
    Send the `subscribeState` message type to central_hub.

    `subscriptionNames` should be an array of keys to subscribe or "*"
    to subscribe to all keys.
    """
    message = SubscribeMessage(data=subscriptionNames)
    await send_message(websocket, message)


async def send_get_state(websocket: Any, keys: Optional[List[str]] = None) -> None:
    """
    Send the `getState` message type to central_hub optionally specifying a list
    of keys to get the state.
    """
    message = GetStateMessage(data=keys)
    await send_message(websocket, message)


async def send_update_state(websocket: Any, stateData: Dict[str, Any]) -> None:
    """
    Send the `updateState` message type to central_hub with the key->value state data to update.
    """
    message = StateUpdateMessage(data=stateData)
    await send_message(websocket, message)
