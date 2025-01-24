import time
from unittest.mock import Mock

import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as bbss
from basic_bot.commons.hub_state_monitor import HubStateMonitor
from basic_bot.commons.hub_state import HubState


def setup_module():
    bbss.start_services(["-m basic_bot.services.central_hub"])


def teardown_module():
    bbss.stop_services(["-m basic_bot.services.central_hub"])


# This may need adjusting.
#
# This is the test running on my mac pro m3, not sure if 10ms latency
# is a reasonable time for the monitor to connect and get the initial state
# and receive the updates after updating.
EXPECTED_LATENCY = 0.01  # seconds


class TestHubStateMonitor:

    def test_updates_with_initial(self):
        INITIAL_FOO = "bar"
        UPDATED_FOO = "baz"

        ws_client = hub.connect()
        hub.send_identity(
            ws_client, "TestHubStateMonitor-test_hub_state_monitor-client1"
        )
        # create the client and send an update before creating the monitor
        hub.send_state_update(ws_client, {"foo": INITIAL_FOO})

        callback = Mock()

        hub_state = HubState({"foo": 0})
        monitor = HubStateMonitor(
            hub_state=hub_state,
            identity="TestHubStateMonitor-test_hub_state_monitor-hub",
            subscribed_keys=["foo"],
            on_state_update=callback,
        )
        monitor.start()

        try:
            # reasonable time for the monitor to connect and get the initial state
            time.sleep(EXPECTED_LATENCY)
            callback.assert_called_once_with(
                monitor.connected_socket,
                "state",
                # {"foo": "this should fail"},  # to test the test
                {"foo": INITIAL_FOO},
            )
            assert hub_state.state.get("foo") == INITIAL_FOO
            callback.reset_mock()

            hub.send_state_update(ws_client, {"foo": UPDATED_FOO})
            # reasonable time for the monitor to get the update and hubstate monitor
            # to call the callback
            time.sleep(EXPECTED_LATENCY)
            callback.assert_called_once_with(
                monitor.connected_socket,
                "stateUpdate",
                {"foo": UPDATED_FOO},
            )
            assert hub_state.state.get("foo") == UPDATED_FOO

        finally:
            # must do this at the end to stop the monitor
            monitor.stop()
