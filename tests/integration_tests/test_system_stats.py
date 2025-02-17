import time
import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as sst

# we're going to set this a bit higher frequency than is normally
# needed in production to speed up the test run time
TEST_SAMPLE_INTERVAL = 0.2  # seconds


def setup_module():
    # start the central hub and any other services needed to test your service
    sst.start_service("central_hub", "python -m basic_bot.services.central_hub")
    sst.start_service(
        "system_stats",
        "python -m basic_bot.services.system_stats",
        {"BB_SYSTEM_STATS_SAMPLE_INTERVAL": TEST_SAMPLE_INTERVAL},
    )


def teardown_module():
    sst.stop_service("central_hub")
    sst.stop_service("system_stats")


class TestSystemStats:
    def test_system_stats(self):
        ws = hub.connect()
        hub.send_identity(ws, "system stats test")
        hub.send_subscribe(ws, ["system_stats"])

        response = hub.recv(ws)
        assert response["type"] == "iseeu"

        # after the first iseeu message all messages should be state updates
        last_cpu_util = 0
        for _i in range(5):
            message = hub.recv(ws)
            assert message["type"] == "stateUpdate"
            cpu_util = message["data"]["system_stats"]["cpu_util"]

            assert cpu_util >= 0
            assert cpu_util <= 100
            assert cpu_util != last_cpu_util
            last_cpu_util = cpu_util

            # as long as the service sleeps the same amount of time that
            # the test sleeps we should get a new system stats message each time
            time.sleep(TEST_SAMPLE_INTERVAL)

        ws.close()
