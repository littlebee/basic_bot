"""
Integration tests for central_hub outbound client connections.

These tests verify bidirectional hub-to-hub communication through outbound
websocket connections.
"""

import time
import yaml
import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as sst
from basic_bot.test_helpers.mock_outbound_client import MockOutboundClient

# semi-random values to use for testing
TEST_ANGLES_1 = [10, 50, 180, 120, 90, 0]
TEST_ANGLES_2 = [15, 55, 175, 115, 95, 5]
TEST_ANGLES_3 = [20, 60, 170, 110, 100, 10]


def setup_module():
    """Setup central_hub service with test config."""
    # Create test config with outbound clients
    with open("basic_bot.yml", "r") as f:
        original_config = f.read()
        config = yaml.safe_load(original_config)

    # Add outbound client configuration
    config["outbound_clients"] = [
        {
            "name": "test_remote_hub",
            "uri": "ws://localhost:5200",
            "identity": "test_outbound_client",
        }
    ]

    # Write test config
    test_config_path = "basic_bot_test_outbound.yml"
    with open(test_config_path, "w") as f:
        yaml.dump(config, f)

    # Start central_hub with test config
    sst.start_service(
        "central_hub",
        "python -m basic_bot.services.central_hub",
        {"BB_CONFIG_FILE": test_config_path},
    )


def teardown_module():
    """Stop central_hub service and cleanup test config."""
    import os

    sst.stop_service("central_hub")

    # Cleanup test config
    test_config_path = "basic_bot_test_outbound.yml"
    if os.path.exists(test_config_path):
        os.remove(test_config_path)


class TestOutboundClients:
    """Test outbound client connections for bidirectional hub communication."""

    def test_outbound_connection_and_identity(self):
        """Test that outbound client connects and sends identity."""
        # Start mock outbound client endpoint
        mock_client = MockOutboundClient(port=5200)
        mock_client.start()

        try:
            # Wait for connection (central_hub retries every 5 seconds)
            assert mock_client.wait_for_connection(timeout=10.0), "Outbound client did not connect"

            # Give a moment for identity exchange to complete
            time.sleep(0.5)

            # Check that identity was received
            assert mock_client.has_received_identity(
                "test_outbound_client"
            ), "Identity message not received or incorrect"

        finally:
            mock_client.stop()

    def test_local_to_remote_state_propagation(self):
        """Test that local state updates are forwarded to remote hub."""
        mock_client = MockOutboundClient(port=5200)
        mock_client.start()

        try:
            # Give central_hub time to connect
            time.sleep(1)

            # Wait for connection
            assert mock_client.wait_for_connection(timeout=5.0)

            # Clear any initial messages
            mock_client.clear_received_messages()

            # Connect local client and send state update
            ws = hub.connect("test_local_client")
            hub.send_update_state(ws, {"set_angles": TEST_ANGLES_1})

            # Wait a bit for propagation
            time.sleep(0.5)

            # Check that remote hub received the state update
            assert mock_client.has_received_state_update(
                "set_angles", TEST_ANGLES_1
            ), "State update not forwarded to remote hub"

            ws.close()

        finally:
            mock_client.stop()

    def test_remote_to_local_state_propagation(self):
        """Test that remote state updates are forwarded to local clients."""
        mock_client = MockOutboundClient(port=5200)
        mock_client.start()

        try:
            # Give central_hub time to connect
            time.sleep(1)

            # Wait for connection
            assert mock_client.wait_for_connection(timeout=5.0)

            # Connect local client and subscribe
            ws = hub.connect("test_local_client")
            hub.send_subscribe(ws, ["current_angles"])

            # Give subscription time to register
            time.sleep(1.0)

            # Remote hub sends state update
            mock_client.send_state_update({"current_angles": TEST_ANGLES_2})

            # Give more time for propagation
            time.sleep(1.0)

            # Local client should receive the update
            assert hub.has_received_state_update(
                ws, "current_angles", TEST_ANGLES_2
            ), "State update from remote hub not received by local client"

            ws.close()

        finally:
            mock_client.stop()

    def test_bidirectional_state_sync(self):
        """Test bidirectional state synchronization between local and remote."""
        mock_client = MockOutboundClient(port=5200)
        mock_client.start()

        try:
            # Give central_hub time to connect
            time.sleep(1)

            # Wait for connection
            assert mock_client.wait_for_connection(timeout=5.0)
            mock_client.clear_received_messages()

            # Setup two local clients
            ws1 = hub.connect("test_local_1")
            hub.send_subscribe(ws1, ["set_angles", "current_angles"])

            ws2 = hub.connect("test_local_2")
            hub.send_subscribe(ws2, ["current_angles"])

            time.sleep(0.5)

            # Local client 1 sends update - should reach local client 2 and remote hub
            hub.send_update_state(ws1, {"set_angles": TEST_ANGLES_1})
            time.sleep(0.5)

            assert hub.has_received_state_update(ws1, "set_angles", TEST_ANGLES_1)
            assert mock_client.has_received_state_update("set_angles", TEST_ANGLES_1)

            # Remote hub sends update - should reach both local clients
            mock_client.send_state_update({"current_angles": TEST_ANGLES_2})
            time.sleep(1.0)

            assert hub.has_received_state_update(ws1, "current_angles", TEST_ANGLES_2)
            assert hub.has_received_state_update(ws2, "current_angles", TEST_ANGLES_2)

            # Local client 2 sends update - should reach client 1 and remote hub
            mock_client.clear_received_messages()
            hub.send_update_state(ws2, {"current_angles": TEST_ANGLES_3})
            time.sleep(0.5)

            assert hub.has_received_state_update(ws1, "current_angles", TEST_ANGLES_3)
            assert mock_client.has_received_state_update("current_angles", TEST_ANGLES_3)

            ws1.close()
            ws2.close()

        finally:
            mock_client.stop()
