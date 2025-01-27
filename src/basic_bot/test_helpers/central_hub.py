import json
from typing import Optional, Dict, Any, List

import basic_bot.commons.constants as c
import basic_bot.test_helpers.constants as tc


# Note this is actually the websocket_client and not the websockets lib.
# websocket_client provides a way of synchronously sending and receiving
# ws messages.  See: https://pypi.org/project/websocket-client/
# `conda install -c conda-forge websocket-client`
import websocket

websocket.enableTrace(True)


def connect(identity: Optional[str] = None) -> websocket.WebSocket:
    """connect to central hub and return a websocket (websocket-client lib)"""
    ws = websocket.create_connection(c.BB_HUB_URI, timeout=tc.DEFAULT_TIMEOUT)

    if identity:
        send(ws, {"type": "identity", "data": identity})
        # clear the iseeu response
        assert recv(ws)

    return ws


def send(ws: websocket.WebSocket, dict: Dict[str, Any]) -> None:
    """send dictionary as json to central hub"""
    ws.send(json.dumps(dict))


def send_get_state(ws: websocket.WebSocket, namesList: List[str]) -> None:
    send(
        ws,
        {
            "type": "getState",
            "data": namesList,
        },
    )


def send_update_state(ws: websocket.WebSocket, dict: Dict[str, Any]) -> None:
    send(
        ws,
        {
            "type": "updateState",
            "data": dict,
        },
    )


def send_identity(ws: websocket.WebSocket, name: str) -> None:
    send(ws, {"type": "identity", "data": name})


def send_subscribe(ws: websocket.WebSocket, namesList: List[str]) -> None:
    send(ws, {"type": "subscribeState", "data": namesList})


def recv(ws: websocket.WebSocket) -> Dict[str, Any]:
    message = json.loads(ws.recv())
    print(f"test helper received: {message}")
    return message


def has_received_data(ws: websocket.WebSocket) -> Optional[Dict[str, Any]]:
    # note zero doesn't work here because it causes it creates a non blocking socket
    # plus we need to give central hub chance to reply for test purposes
    ws.settimeout(0.1)
    try:
        return recv(ws)
    except websocket._exceptions.WebSocketTimeoutException:
        return None
    finally:
        ws.settimeout(tc.DEFAULT_TIMEOUT)


def has_received_state_update(ws: websocket.WebSocket, key: str, value: Any) -> bool:
    stateUpdate = recv(ws)
    return stateUpdate["type"] == "stateUpdate" and stateUpdate["data"][key] == value
