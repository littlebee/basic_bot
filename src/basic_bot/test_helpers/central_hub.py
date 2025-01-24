import json

import basic_bot.commons.constants as c
import basic_bot.test_helpers.constants as tc


# Note this is actually the websocket_client and not the websockets lib.
# websocket_client provides a way of synchronously sending and receiving
# ws messages.  See: https://pypi.org/project/websocket-client/
# `conda install -c conda-forge websocket-client`
import websocket

websocket.enableTrace(True)


def connect(identity=None):
    """connect to central hub and return a websocket (websocket-client lib)"""
    ws = websocket.create_connection(c.BB_HUB_URI, timeout=tc.DEFAULT_TIMEOUT)

    if identity:
        send(ws, {"type": "identity", "data": identity})
        # clear the iseeu response
        assert recv(ws)

    return ws


def send(ws, dict):
    """send dictionary as json to central hub"""
    return ws.send(json.dumps(dict))


def send_state_update(ws, dict):
    send(
        ws,
        {
            "type": "updateState",
            "data": dict,
        },
    )


def send_identity(ws, name):
    send(ws, {"type": "identity", "data": name})


def send_subscribe(ws, namesList):
    send(ws, {"type": "subscribeState", "data": namesList})


def recv(ws):
    message = json.loads(ws.recv())
    print(f"test helper received: {message}")
    return message


def has_received_data(ws):
    # note zero doesn't work here because it causes it creates a non blocking socket
    # plus we need to give central hub chance to reply for test purposes
    ws.settimeout(0.1)
    try:
        return recv(ws)
    except websocket._exceptions.WebSocketTimeoutException:
        return False
    finally:
        ws.settimeout(tc.DEFAULT_TIMEOUT)


def has_received_state_update(ws, key, value):
    stateUpdate = recv(ws)
    return stateUpdate["type"] == "stateUpdate" and stateUpdate["data"][key] == value
