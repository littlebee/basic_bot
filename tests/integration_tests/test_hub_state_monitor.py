import time
import threading
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
        hub.send_update_state(ws_client, {"foo": INITIAL_FOO})

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

            hub.send_update_state(ws_client, {"foo": UPDATED_FOO})
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

    def test_on_connect(self):

        on_connect = Mock()
        monitor = HubStateMonitor(
            hub_state=HubState({"foo": 0}),
            identity="TestHubStateMonitor-test_hub_state_monitor-hub",
            subscribed_keys=["foo"],
            on_connect=on_connect,
        )
        monitor.start()

        try:
            time.sleep(EXPECTED_LATENCY)
            on_connect.assert_called_once_with(monitor.connected_socket)
        finally:
            monitor.stop()

    def test_round_trip_latency(self):
        MESSAGES_TO_SEND = 100
        connected = threading.Event()
        connected.clear()

        self.recvd_all = threading.Event()
        self.recvd_all.clear()

        self.recv_count = 0
        self.recv_latencies = []

        def on_state_update(
            _ws,
            msg_type,
            data,
        ):
            if msg_type != "stateUpdate":
                return
            print(f"on_state_update: {data}")
            self.recv_latencies.append(time.time() - data["time_sent"])
            self.recv_count += 1
            if self.recv_count == MESSAGES_TO_SEND:
                self.recvd_all.set()

        monitor = HubStateMonitor(
            hub_state=HubState({"time_sent": 0}),
            identity="TestHubStateMonitor-latency_test_monitor",
            subscribed_keys=["time_sent"],
            on_state_update=on_state_update,
            on_connect=lambda _: connected.set(),
        )
        monitor.start()

        print("test waiting for monitor connection")
        connected.wait()

        overall_start = time.time()
        ws_client = hub.connect("TestHubStateMonitor-latency_test_client")
        for _i in range(0, MESSAGES_TO_SEND):
            hub.send_update_state(ws_client, {"time_sent": time.time()})
            # minimal sleep to allow the hub state monitor thread to have a chance to
            # process messages
            time.sleep(0.0001)

        print(f"{MESSAGES_TO_SEND} messages sent, waiting for all to be received")
        self.recvd_all.wait()
        print("all messages received")

        overall_duration = time.time() - overall_start
        assert len(self.recv_latencies) == MESSAGES_TO_SEND  # sanity check

        avg_latency = sum(self.recv_latencies) / len(self.recv_latencies)
        print(f"average latency: {avg_latency}")
        print(f"{self.recv_latencies=}")
        print(f"{overall_duration=}")

        sorted_data = sorted(self.recv_latencies)
        p90_index = int(0.9 * len(sorted_data))
        p90_value = sorted_data[p90_index]
        relevant_data = [x for x in sorted_data if x <= p90_value]

        p90_latency = sum(relevant_data) / len(relevant_data)
        print(f"p90 latency: {p90_latency}")

        throughput = MESSAGES_TO_SEND / overall_duration
        print(f"throughput: {throughput} messsages per second")

        assert p90_latency < EXPECTED_LATENCY
        assert throughput > 1000

        monitor.stop()
