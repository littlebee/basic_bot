"""
Mock outbound client endpoint for testing outbound connections.

This module provides a mock websocket server that simulates a remote endpoint
for testing the outbound client functionality.
"""

import asyncio
import json
import threading
import time
from typing import Optional, List, Dict, Any
from websockets.server import WebSocketServerProtocol
import websockets


class MockOutboundClient:
    """
    A mock websocket server that simulates a remote outbound client endpoint.

    Used for testing outbound client connections and bidirectional communication.
    """

    def __init__(self, port: int = 5200):
        self.port = port
        self.server = None
        self.server_task: Optional[asyncio.Task] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected_clients: List[WebSocketServerProtocol] = []
        self.received_messages: List[Dict[str, Any]] = []
        self.identity_received: Optional[str] = None
        self.running = False
        self.connection_event = threading.Event()

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle incoming websocket connection from central_hub's outbound client."""
        print(f"MockOutboundClient: Client connected from {websocket.remote_address}")
        self.connected_clients.append(websocket)
        self.connection_event.set()

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"MockOutboundClient received: {data}")
                    self.received_messages.append(data)

                    # Handle identity message
                    if data.get("type") == "identity":
                        identity_data = data.get("data")
                        if isinstance(identity_data, dict):
                            self.identity_received = identity_data.get("subsystem_name")
                        else:
                            self.identity_received = identity_data
                        print(
                            f"MockOutboundClient: Received identity: {self.identity_received}"
                        )

                    # Handle ping
                    elif data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))

                except json.JSONDecodeError as e:
                    print(f"MockOutboundClient: Failed to parse message: {e}")

        except Exception as e:
            print(f"MockOutboundClient: Connection error: {e}")
        finally:
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
            print("MockOutboundClient: Client disconnected")

    async def _run_server(self):
        """Run the websocket server."""
        print(f"MockOutboundClient: Starting server on port {self.port}")
        async with websockets.serve(
            self._handle_client, "localhost", self.port
        ) as server:
            self.server = server
            self.running = True
            # Wait until stopped
            while self.running:
                await asyncio.sleep(0.1)

    def _run_in_thread(self):
        """Run the server in a separate thread with its own event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._run_server())
        except Exception as e:
            if "Event loop stopped" not in str(e):
                print(f"MockOutboundClient: Server error: {e}")
        finally:
            # Clean up pending tasks
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            self.loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )
            self.loop.close()

    def start(self):
        """Start the mock outbound client server in a background thread."""
        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()
        # Give server time to start
        time.sleep(0.5)

    def stop(self):
        """Stop the mock outbound client server."""
        print("MockOutboundClient: Stopping server")
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)

    def wait_for_connection(self, timeout: float = 5.0) -> bool:
        """
        Wait for an outbound client to connect.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if connection established, False if timeout.
        """
        return self.connection_event.wait(timeout)

    def send_state_update(self, state_data: Dict[str, Any]):
        """
        Send a state update to all connected clients.

        Args:
            state_data: Dictionary of state key/value pairs to send.
        """
        if not self.connected_clients:
            print("MockOutboundClient: No clients connected, cannot send state update")
            return

        message = {"type": "updateState", "data": state_data}
        message_str = json.dumps(message)

        async def _send():
            for client in self.connected_clients:
                try:
                    await client.send(message_str)
                    print(f"MockOutboundClient: Sent state update: {state_data}")
                except Exception as e:
                    print(f"MockOutboundClient: Failed to send to client: {e}")

        if self.loop:
            future = asyncio.run_coroutine_threadsafe(_send(), self.loop)
            # Wait for the send to complete
            try:
                future.result(timeout=2)
            except Exception as e:
                print(f"MockOutboundClient: Error waiting for send: {e}")

    def get_received_messages(self) -> List[Dict[str, Any]]:
        """Get all messages received from connected clients."""
        return self.received_messages.copy()

    def clear_received_messages(self):
        """Clear the received messages list."""
        self.received_messages.clear()

    def has_received_identity(self, expected_name: Optional[str] = None) -> bool:
        """
        Check if identity message was received.

        Args:
            expected_name: Optional specific subsystem name to check for.

        Returns:
            True if identity received (and matches expected_name if provided).
        """
        if expected_name:
            return self.identity_received == expected_name
        return self.identity_received is not None

    def has_received_state_update(self, key: str, value: Any) -> bool:
        """
        Check if a specific state update was received.

        Args:
            key: The state key to check for.
            value: The expected value.

        Returns:
            True if matching state update found.
        """
        for message in self.received_messages:
            if message.get("type") == "stateUpdate":
                data = message.get("data", {})
                if key in data and data[key] == value:
                    return True
        return False

    def get_state_updates(self) -> List[Dict[str, Any]]:
        """
        Get all state update messages received.

        Returns:
            List of state update data dictionaries.
        """
        return [
            msg.get("data", {})
            for msg in self.received_messages
            if msg.get("type") == "stateUpdate"
        ]
