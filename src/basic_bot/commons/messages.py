import json
from enum import Enum
from typing import Optional, List, Dict, Any

from basic_bot.commons import log, constants as c


class MessageType(Enum):
    STATE_UPDATE = "stateUpdate"
    STATE = "state"
    IDENTITY = "iseeu"


async def send_message(websocket: Any, message: Dict[str, Any]) -> None:
    json_message = json.dumps(message)
    if c.BB_LOG_ALL_MESSAGES:
        log.info(f"sent {json_message} to {websocket.remote_address[1]}")
    await websocket.send(json_message)


async def send_identity(websocket: Any, name: str) -> None:
    await send_message(
        websocket,
        {
            "type": "identity",
            "data": name,
        },
    )


# subscriptionNames should be an array or "*"
async def send_subscribe(websocket: Any, subscriptionNames: List[str]) -> None:
    await send_message(
        websocket,
        {
            "type": "subscribeState",
            "data": subscriptionNames,
        },
    )


async def send_get_state(websocket: Any, keys: Optional[List[str]] = []) -> None:
    await send_message(
        websocket,
        {
            "type": "getState",
            "data": keys,
        },
    )


async def send_update_state(websocket: Any, stateData: Dict[str, Any]) -> None:
    await send_message(
        websocket,
        {
            "type": "updateState",
            "data": stateData,
        },
    )
