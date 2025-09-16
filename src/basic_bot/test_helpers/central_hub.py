import json
from typing import Optional, Dict, Any, List

import basic_bot.commons.constants as c
import basic_bot.test_helpers.constants as tc


# Note this is actually the websocket_client and not the websockets lib.
# websocket_client provides a way of synchronously sending and receiving
# ws messages.  See: https://pypi.org/project/websocket-client/
# `conda install -c conda-forge websocket-client`
import websocket
from websocket import WebSocket

websocket.enableTrace(True)


def connect(identity: Optional[str] = None) -> WebSocket:
    """connect to central hub and return a websocket (websocket-client lib)"""
    ws: WebSocket = websocket.create_connection(c.BB_HUB_URI, timeout=tc.DEFAULT_TIMEOUT)

    if identity:
        send(ws, {"type": "identity", "data": identity})
        # clear the iseeu response
        response = recv(ws)
        assert response

    return ws


def send(ws: WebSocket, dict: Dict[str, Any]) -> None:
    """send dictionary as json to central hub"""
    ws.send(json.dumps(dict))


def send_get_state(ws: WebSocket, namesList: List[str]) -> None:
    send(
        ws,
        {
            "type": "getState",
            "data": namesList,
        },
    )


def send_update_state(ws: WebSocket, dict: Dict[str, Any]) -> None:
    send(
        ws,
        {
            "type": "updateState",
            "data": dict,
        },
    )


def send_identity(ws: WebSocket, name: str) -> None:
    send(ws, {"type": "identity", "data": name})


def send_subscribe(ws: WebSocket, namesList: List[str]) -> None:
    send(ws, {"type": "subscribeState", "data": namesList})


def recv(ws: WebSocket) -> Dict[str, Any]:
    message_str = ws.recv()
    message: Dict[str, Any] = json.loads(message_str)
    print(f"test helper received: {message}")
    return message


def has_received_data(ws: WebSocket) -> Optional[Dict[str, Any]]:
    # note zero doesn't work here because it causes it creates a non blocking socket
    # plus we need to give central hub chance to reply for test purposes
    ws.settimeout(0.1)
    try:
        return recv(ws)
    except websocket._exceptions.WebSocketTimeoutException:
        return None
    finally:
        ws.settimeout(tc.DEFAULT_TIMEOUT)


def has_received_state_update(ws: WebSocket, key: str, value: Any) -> bool:
    while True:
        message = recv(ws)
        if message["type"] == "stateUpdate" and key in message["data"]:
            break

    state_update_data: Dict[str, Any] = message["data"]
    received_value: Any = state_update_data.get(key)
    return bool(received_value == value)
