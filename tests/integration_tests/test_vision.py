import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as bbss


def setup_module():
    bbss.start_services(
        ["-m basic_bot.services.central_hub", "-m basic_bot.services.vision"]
    )


def teardown_module():
    bbss.stop_services(
        ["-m basic_bot.services.central_hub", "-m basic_bot.services.vision"]
    )


class TestVisionCV2:
    def test_object_detection(self):
        ws = hub.connect()
        # this name shows up in central hub logs and is helpful for debugging
        hub.send_identity(ws, "TestVisionCV2:test_object_detection")
        response = hub.recv(ws)
        assert response["type"] == "iseeu"
        hub.send_subscribe(ws, ["recognition"])

        ws.close()
