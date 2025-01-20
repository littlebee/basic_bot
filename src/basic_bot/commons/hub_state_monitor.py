"""
This class updates the local copy of the hub state as subscribed keys are changed.

A thread is created to listen for state updates from the central hub.
When a state update is received, the local state is updated and the
state_updated_at timestamp is updated.
"""

import threading
import asyncio
import websockets
import traceback
import json
from typing import Callable, Optional, List

from basic_bot.commons import constants, messages, log


class HubStateMonitor:
    """
    This class updates the process local copy of the hub state as subscribed keys
    are changed.  It starts a thread to listen for state updates from the central
    hub and applies them to the local state via hub_state.update_state_from_message_data.
    """

    def __init__(
        self,
        hub_state: dict,
        identity: str,
        subscribed_keys: List[str],
        on_message_recv: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.hub_state = hub_state
        self.identity = identity
        self.subscribed_keys = subscribed_keys
        self.on_message_recv = on_message_recv

        # background thread connects to central_hub and listens for state updates
        self.thread = threading.Thread(target=self._thread)

        # web socket if we are connected, None otherwise
        self.connected_socket: Optional[websockets.WebSocketClientProtocol] = None

        self.thread.start()

    async def monitor_state(self) -> None:
        while True:
            try:
                log.info(
                    f"hub_state_monitor connecting to hub central at {constants.BB_HUB_URI}"
                )
                async with websockets.connect(constants.BB_HUB_URI) as websocket:
                    self.connected_socket = websocket
                    await messages.send_identity(websocket, self.identity)
                    await messages.send_get_state(websocket)
                    await messages.send_subscribe(websocket, self.subscribed_keys)
                    async for message in websocket:
                        data = json.loads(message)
                        if self.on_message_recv:
                            self.on_message_recv(data)
                        if data.get("type") == "state":
                            message_data = data.get("data")
                            self.hub_state.update_state_from_message_data(message_data)
                        await asyncio.sleep(0)

            except:
                traceback.print_exc()

            self.connected_socket = None
            log.info("central_hub socket disconnected.  Reconnecting in 5 sec...")
            await asyncio.sleep(5)

    def _thread(self):
        log.info("Starting hub_state_monitor thread.")
        asyncio.run(self.monitor_state())
