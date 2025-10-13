"""
This module is used by central_hub to manage connections to external hub clients
that cannot directly inbound connect to the central_hub websocket.
"""

import asyncio
import websockets.client
from websockets.client import WebSocketClientProtocol

from basic_bot.commons import log, constants as c
from basic_bot.commons.config_file import read_config_file

from typing import Optional, Callable, Any, Dict, Union


class OutboundClients:
    """
    This class manages outbound websocket connections to external hub clients
    that cannot directly inbound connect to the central_hub websocket.

    It features automatic reconnection on connection loss.
    """

    def __init__(
        self,
        on_message_received: Optional[Callable[[Any, Union[str, bytes]], Any]] = None,
    ) -> None:
        config = read_config_file(c.BB_CONFIG_FILE)
        self.outbound_clients = config.get("outbound_clients", [])
        self.connections: Dict[str, WebSocketClientProtocol] = {}
        self.on_message_received = on_message_received
        self.is_stopping = False

    async def connect_all(self) -> None:
        """
        Connects to all outbound clients specified in the configuration.
        """
        for client in self.outbound_clients:
            name = client["name"]
            uri = client["uri"]
            identity = client["identity"]
            shared_token_file = client.get("shared_token_file")

            token = None
            if shared_token_file:
                try:
                    with open(shared_token_file, "r") as f:
                        token = f.read().strip()
                except Exception as e:
                    log.error(f"Failed to read token from {shared_token_file}: {e}")

            asyncio.create_task(self._connect_and_listen(name, uri, identity, token))

    def stop(self) -> None:
        """
        Stops all outbound client connections.
        """
        self.is_stopping = True
        for name, websocket in self.connections.items():
            asyncio.create_task(websocket.close())
        self.connections.clear()

    async def _connect_and_listen(
        self, name: str, uri: str, identity: str, token: Optional[str]
    ) -> None:
        """
        Connects to a single outbound client and listens for messages.

        Args:
            name (str): The unique name of the outbound client.
            uri (str): The websocket URI of the outbound client.
            identity (str): The identity string to send upon connection.
            token (Optional[str]): An optional shared secret token for authentication.
        """
        while not self.is_stopping:
            try:
                log.info(f"Connecting to outbound client {name} at {uri}")
                async with websockets.client.connect(uri) as websocket:  # type: ignore
                    self.connections[name] = websocket
                    await self._send_identity(websocket, identity, token)
                    await self._listen(websocket, name)
            except Exception as e:
                log.error(f"Connection to {name} failed: {e}")
                log.info(f"Reconnecting to {name} in 5 seconds...")
                await asyncio.sleep(5)

    async def _send_identity(
        self, websocket, identity: str, token: Optional[str]
    ) -> None:
        """
        Sends an identity message to the remote websocket server.

        Args:
            websocket: The websocket connection.
            identity (str): The identity string to send.
            token (Optional[str]): An optional shared secret token for authentication.
        """
        import json

        identity_data = {"subsystem_name": identity}
        if token:
            identity_data["shared_token"] = token

        message = json.dumps({"type": "identity", "data": identity_data})
        await websocket.send(message)
        log.info(f"Sent identity: {identity}")

    async def _listen(self, websocket, name: str) -> None:
        """
        Listens for messages from the remote websocket server and forwards
        all messages to the callback.

        Args:
            websocket: The websocket connection.
            name (str): The name of the outbound client.
        """
        try:
            async for message in websocket:
                log.debug(f"Received message from outbound client {name}")
                # Forward all messages to the callback for processing
                if self.on_message_received:
                    await self.on_message_received(websocket, message)
        except Exception as e:
            log.error(f"Error in _listen for {name}: {e}")
            raise

    async def broadcast(self, message: str) -> None:
        """
        Broadcasts a message to all connected outbound clients.

        Args:
            message (str): The JSON message to send.
        """
        for name, websocket in self.connections.items():
            try:
                await websocket.send(message)
            except Exception as e:
                log.error(f"Failed to broadcast to {name}: {e}")
