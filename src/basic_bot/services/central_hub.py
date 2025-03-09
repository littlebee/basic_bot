#!/usr/bin/env python3
"""
Provides an ultra-light pub/sub service with < 5ms latecy over
websockets.  The state of published keys is maintained in memory.

This python process is meant to be run as a service by basic_bot.

You can also run it in the foreground for debugging purposes.  ex:
```sh
python -m basic_bot.services.central_hub
```

Central hub is also the publisher of several state keys:
```json
{
    "hub_stats": {
        "state_updates_recv": 0
    },
    "subsystem_stats": {}
}
```
## Messages

All data sent over the websocket to and from central_hub is in json and has the format:
```json
{
     "type": "string",
     "data": { ... }
}
```
Where `data` is optional and specific to the type of message. The following messages are supported by `central-hub`:

#### getState

example json:

```json
{
  "type": "getState"
  "data": ["keyName", "keyName"]
}
```
Causes `central-hub` to send the requested state via message type = "state" to the requesting client socket.

`data` is optional, if specified, should be array of key names to retrieve. If omitted, all keys (complete state) is sent.


### identity

example json:

```json
{
  "type": "identity",
  "data": "My subsystem name"
}
```

Causes `central-hub` to update `subsystems_stats` key of the shared state and send an "iseeu" message back to client socket with the IP address that it sees the client.

### subscribeState

example json:

```json
{
  "type": "subscribeState",
  "data": ["system_stats", "set_angles"]
}
```

Causes `central-hub` to add the client socket to the subscribers for each of the state keys provided. Client will start receiving "stateUpdate" messages when those keys are changed. The client may also send `"data": "*"` which will subscribe it to all keys like the web UI does.

### updateState

example json:

```json
{
  "type": "updateState",
  "data": {
    "set_angles": [127.4, 66.4, 90, 90, 0],
    "velocity_factor": 1.5
  }
}
```

This message causes `central-hub` merge the receive state and the shared
state and send `stateUpdate` messages to any subscribers. Note that the
message sent by clients** (type: "updateState") is a different type than
the message **sent to clients** (type: "stateUpdate").

As the example above shows, it is possible to update multiple state keys at
once, but most subsystems only ever update one top level key.

The data received must be the **full data for that key**. `central-hub`
will replace that top level key with the data received.



"""
import json
import asyncio
import websockets
import traceback
from typing import Any, Dict, List, Optional

from websockets.server import WebSocketServerProtocol

from basic_bot.commons import constants, log
from basic_bot.commons.hub_state import HubState


log.info("Initializing hub state")
hub_state = HubState(
    {
        # provided by central_hub/
        "hub_stats": {"state_updates_recv": 0},
        # which subsystems are online and have indentified themselves
        "subsystem_stats": {},
    },
)

# these are all of the client sockets that are connected to the hub
connected_sockets: set[WebSocketServerProtocol] = set()

# a dictionary of sets containing sockets by top level
# dictionary key in hub_state to which they are subscribed
subscribers: Dict[str, set[WebSocketServerProtocol]] = dict()

# a set of websockets that subscribed to all keys using "*"
star_subscribers: set[WebSocketServerProtocol] = set()

# a dictionary of websocket to subsystem name; see handle_identity
identities: Dict[WebSocketServerProtocol, str] = dict()


def iseeu_message(websocket: WebSocketServerProtocol) -> str:
    return json.dumps(
        {
            "type": "iseeu",
            "data": {
                "ip": websocket.remote_address[0],
                "port": websocket.remote_address[1],
            },
        }
    )


async def send_message(websocket: WebSocketServerProtocol, message: str) -> None:
    if constants.BB_LOG_ALL_MESSAGES and message != '{"type": "pong"}':
        log.info(
            f"sending {message} to {websocket.remote_address[0]}:{websocket.remote_address[1]}"
        )
    if websocket and websocket != "all":
        await websocket.send(message)
    elif connected_sockets:  # asyncio.wait doesn't accept an empty list
        # The type ignore is to suppress the mypy error below when running on linux:
        #    Value of type variable "_FT" of "wait" cannot be "Coroutine[Any, Any, None]"  [type-var]
        #
        # mypy on the mac doesn't have this issue.  Looking at the type definition for asyncio.wait,
        # it looks like mypy on the linux (Python 3.11.2) doesn't realize that there is an overload
        # that takes an iterable of coroutines: `fs: Iterable[Awaitable[_T]]`
        await asyncio.wait([websocket.send(message) for websocket in connected_sockets])  # type: ignore


async def send_state_update_to_subscribers(message_data: Dict[str, Any]) -> None:
    subscribed_sockets: set[WebSocketServerProtocol] = set()
    for key in message_data:
        # really need to keep this tight as possible,  don't log here
        # unless needed to debug
        # log.info(f"subscribed sockets for {key}: {subscribers[key]}")
        for sub_socket in subscribers.get(key) or []:
            subscribed_sockets.add(sub_socket)

        for sub_socket in star_subscribers:
            subscribed_sockets.add(sub_socket)

    if len(subscribed_sockets) == 0:
        log.info(
            f"send_state_update_to_subscribers: no subscribers for {message_data.keys()}"
        )
        return

    relay_message = json.dumps(
        {
            "type": "stateUpdate",
            # note that we send the message as received to any subscribers
            # of **any** keys in the message. So if a subsystem sends updates
            # for two keys and a client is subscribed to one of the keys, it
            # will get both keys in the stateUpdate message.
            "data": message_data,
        }
    )
    sockets_to_close: set[WebSocketServerProtocol] = set()
    for socket in subscribed_sockets:
        try:
            await send_message(socket, relay_message)
        except websockets.exceptions.ConnectionClosedOK:
            # if the exception is a websockets.exceptions.ConnectionClosedOK
            # then the client has disconnected and we can remove it from the
            # subscribers list and close the socket, but we don't want to
            # log an error in that case.
            sockets_to_close.add(socket)
        except Exception as e:
            log.info(
                f"error sending message to subscriber {socket.remote_address[1]}: {e}"
            )
            traceback.print_exc()
            sockets_to_close.add(socket)

    for socket in sockets_to_close:
        log.info(f"relay error: closing socket {socket.remote_address[1]}")
        await unregister(socket)
        await socket.close()


async def notify_state(
    websocket: WebSocketServerProtocol,
    keysRequested: Optional[List[str]] = None,
) -> None:
    await send_message(websocket, hub_state.serialize_state(keysRequested))


# NOTE that there is no "all" option here, need a websocket,
#  ye shall not ever broadcast this info
async def notify_iseeu(websocket: WebSocketServerProtocol) -> None:
    if not websocket or websocket == "all":
        return
    await send_message(websocket, iseeu_message(websocket))


async def update_online_status(subsystem_name: str, status: int) -> None:
    if subsystem_name in hub_state.state["subsystem_stats"]:
        hub_state.state["subsystem_stats"][subsystem_name]["online"] = status
    else:
        hub_state.state["subsystem_stats"][subsystem_name] = {"online": status}

    await send_state_update_to_subscribers(
        {"subsystem_stats": hub_state.state["subsystem_stats"]}
    )


async def register(websocket: WebSocketServerProtocol) -> None:
    log.info(
        f"got new connection from {websocket.remote_address[0]}:{websocket.remote_address[1]}:"
    )
    connected_sockets.add(websocket)


async def unregister(websocket: WebSocketServerProtocol) -> None:
    log.info(
        f"lost connection {websocket.remote_address[0]}:{websocket.remote_address[1]}"
    )
    try:
        connected_sockets.remove(websocket)
        star_subscribers.remove(websocket)

        for key in subscribers:
            subscribers[key].remove(websocket)
        subsystem_name = identities.pop(websocket, None)
        if subsystem_name:
            await update_online_status(subsystem_name, 0)
    except:
        pass


async def handle_state_request(
    websocket: WebSocketServerProtocol, keysRequested: Optional[List[str]] = None
) -> None:
    await notify_state(websocket, keysRequested)


async def handle_state_update(message_data: Dict[str, Any]) -> None:
    global subscribers

    log.debug(f"handle_state_update: {message_data}")

    hub_state.update_state_from_message_data(message_data)
    hub_state.state["hub_stats"]["state_updates_recv"] += 1

    await send_state_update_to_subscribers(message_data)


async def handle_state_subscribe(
    websocket: WebSocketServerProtocol, subscription_keys: List[str]
) -> None:
    global subscribers
    global star_subscribers

    if subscription_keys == "*":
        log.debug(f"adding {websocket.remote_address[1]} to star subscribers")
        star_subscribers.add(websocket)
        return

    for key in subscription_keys:
        socket_set: Optional[set[WebSocketServerProtocol]] = None
        if key in subscribers:
            socket_set = subscribers[key]
        else:
            socket_set = set()
            subscribers[key] = socket_set

        log.info(
            f"subscribing {websocket.remote_address[0]}:{websocket.remote_address[1]} to {key}"
        )
        socket_set.add(websocket)


async def handle_state_unsubscribe(
    websocket: WebSocketServerProtocol, data: List[str]
) -> None:
    global subscribers
    subscription_keys: List[str] = []
    if data == "*":
        subscription_keys = list(subscribers.keys())
    else:
        subscription_keys = data

    for key in subscription_keys:
        if key in subscribers:
            subscribers[key].remove(websocket)


async def handle_identity(
    websocket: WebSocketServerProtocol, subsystem_name: str
) -> None:
    identities[websocket] = subsystem_name
    log.info(f"setting identity of {websocket.remote_address[1]} to {subsystem_name}")
    await update_online_status(subsystem_name, 1)
    await notify_iseeu(websocket)


async def handle_ping(websocket: WebSocketServerProtocol) -> None:
    await send_message(websocket, json.dumps({"type": "pong"}))


async def handle_message(websocket: WebSocketServerProtocol) -> None:
    await register(websocket)
    try:
        async for message in websocket:
            try:
                jsonData = json.loads(message)
                messageType = jsonData.get("type")
                messageData = jsonData.get("data")
            except:
                log.error(f"error parsing message: {str(message)}")
                continue

            if constants.BB_LOG_ALL_MESSAGES and messageType != "ping":
                log.info(f"received {str(message)} from {websocket.remote_address[1]}")

            # {type: "getState, data: [state_keys] or omitted}
            if messageType == "getState":
                await handle_state_request(websocket, messageData)
            # {type: "updateState" data: { new state }}
            elif messageType == "updateState":
                await handle_state_update(messageData)
            # {type: "subscribeState", data: [state_keys] or "*"
            elif messageType == "subscribeState":
                await handle_state_subscribe(websocket, messageData)
            # {type: "unsubscribeState", data: [state_keys] or "*"
            elif messageType == "unsubscribeState":
                await handle_state_unsubscribe(websocket, messageData)
            # {type: "identity", data: "subsystem_name"}
            elif messageType == "identity":
                await handle_identity(websocket, messageData)
            elif messageType == "ping":
                await handle_ping(websocket)
            else:
                log.error(f"received unsupported message: {messageType}")

            if constants.BB_LOG_ALL_MESSAGES and messageType != "ping":
                log.info(f"getting next message for {websocket.remote_address[1]}")

    except Exception as e:
        # don't log the exception if it's just a disconnect "no close frame"
        if "no close frame received" not in str(e):
            log.error(f"handle_message from {websocket.remote_address[1]}: {e}")
            traceback.print_exc()
            raise e

    finally:
        await unregister(websocket)
        await websocket.close()


async def main() -> None:
    log.info(f"Starting server on port {constants.BB_HUB_PORT}")
    # TODO : figure out why the type error below
    async with websockets.serve(handle_message, port=constants.BB_HUB_PORT):  # type: ignore
        # log.info("Starting hub stats task")
        # await send_hub_stats_task()
        await asyncio.Future()  # run forever


asyncio.run(main())
