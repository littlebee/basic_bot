import threading
import asyncio
import websockets
import traceback
import json
from contextlib import asynccontextmanager

from typing import Callable, Optional, List, AsyncGenerator, Union, Literal
from websockets.client import WebSocketClientProtocol

from basic_bot.commons import constants as c, messages, log
from basic_bot.commons.hub_state import HubState


# TODO: This class should maybe be a singleton.
should_exit = False


class HubStateMonitor:
    """
    This class updates the process local copy of the hub state as subscribed keys
    are changed.  It starts a thread to listen for state updates from the central
    hub and applies them to the local state via hub_state.update_state_from_message_data.

    Before applying the state update, it calls the on_state_update callback if it is
    provided.  This allows the caller to do something with the state update
    before it is applied to the local state and to see the difference in current state
    vs. to be applied state.

    The state update is applied to the local state via
    hub_state.update_state_from_message_data regardless of whether the on_state_update
    callback is provided or the value it returns.  To alter the state you should
    alway send an `updateState` message to the central hub.

    Usage:
    ```python
    from basic_bot.commons.hub_state import HubState
    from basic_bot.commons.hub_state_monitor import HubStateMonitor

    hub_state = HubState({"test_key": "test_value"})
    monitor = HubStateMonitor(hub_state, "test_identity", ["test_key"])
    monitor.start()
    ```
    The above example will start a background thread that listens for state updates
    to the "test_key" key from the central hub and updates the local state with the
    new value.

    For a more complex example using callbacks, see [usage in daphbot example - daphbot_service](https://github.com/littlebee/daphbot-due/blob/aa7ed90d60df33009c5bd252c31fa0fb25076fad/src/daphbot_service.py#L75)

    """

    def __init__(
        self,
        hub_state: HubState,
        identity: str,
        subscribed_keys: Union[List[str], Literal["*"]],
        on_connect: Optional[
            Callable[
                [WebSocketClientProtocol],
                None,
            ]
        ] = None,
        on_state_update: Optional[
            Callable[
                [
                    WebSocketClientProtocol,
                    str,
                    dict,
                ],
                None,
            ]
        ] = None,
    ) -> None:
        """Instantiate a HubStateMonitor object."""
        self.hub_state = hub_state
        self.identity = identity
        self.subscribed_keys = subscribed_keys
        self.on_state_update = on_state_update
        self.on_connect = on_connect

        # background thread connects to central_hub and listens for state updates
        self.thread = threading.Thread(target=self._thread)

        # web socket if we are connected, None otherwise
        self.connected_socket: Optional[WebSocketClientProtocol] = None

    def start(self) -> None:
        """Starts the background thread that listens for state updates and updates HubState"""
        self.thread.start()

    def stop(self) -> None:
        global should_exit
        """Stops the background thread that listens for state updates and updates HubState"""
        log.info("Stopping hub_state_monitor thread.")
        should_exit = True
        self.connected_socket and self.connected_socket.close()

    @asynccontextmanager
    async def connect_to_hub(
        self,
    ) -> AsyncGenerator[websockets.client.WebSocketClientProtocol, None]:
        log.info(f"hub_state_monitor connecting to central_hub at {c.BB_HUB_URI}")
        async with websockets.client.connect(c.BB_HUB_URI) as websocket:
            log.info("hub_state_monitor connected to central_hub")
            state_keys = self.subscribed_keys if self.subscribed_keys != "*" else None
            self.connected_socket = websocket
            await messages.send_identity(websocket, self.identity)
            await messages.send_subscribe(websocket, self.subscribed_keys)
            await messages.send_get_state(websocket, state_keys)
            yield websocket

    async def parse_next_message(
        self, websocket: WebSocketClientProtocol
    ) -> AsyncGenerator[tuple[str, dict], None]:
        async for message in websocket:
            if should_exit:
                return

            msg = json.loads(message)
            if c.BB_LOG_ALL_MESSAGES:
                log.info(f"hub_state_monitor received: {msg}")
            msg_type = msg.get("type")
            msg_data = msg.get("data")

            yield msg_type, msg_data

            if should_exit:
                return

    async def monitor_state(self) -> None:
        while not should_exit:
            try:
                if should_exit:
                    return  # we want to just exit if we are not running
                async with self.connect_to_hub() as websocket:

                    if self.on_connect:
                        self.on_connect(websocket)

                    async for msg_type, msg_data in self.parse_next_message(websocket):
                        if msg_type in ["state", "stateUpdate"]:
                            """
                            The order here is intentional.  We want the on_state_update
                            to still be able to query the pre-changed state via hub_state
                            if it needs to.  See class comment.
                            """
                            if self.on_state_update:
                                self.on_state_update(websocket, msg_type, msg_data)

                            self.hub_state.update_state_from_message_data(msg_data)

                    if should_exit:
                        return
                    await asyncio.sleep(0)

            except Exception as e:
                if "no close frame received" not in str(e):
                    traceback.print_exc()

            self.connected_socket = None
            log.info("central_hub socket disconnected. Reconnecting in 5 sec...")
            await asyncio.sleep(5)

    def _thread(self) -> None:
        log.info("Starting hub_state_monitor thread.")
        asyncio.run(self.monitor_state())
