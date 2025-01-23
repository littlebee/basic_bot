import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as bbss
import basic_bot.test_helpers.constants as tc

# semi-random values to use for testing
TEST_ANGLES_1 = [10, 50, 180, 120, 90, 0]
TEST_ANGLES_2 = [15, 55, 175, 115, 95, 5]


def setup_module():
    bbss.start_services(
        ["-m basic_bot.services.central_hub", "-m basic_bot.services.vision_cv2"]
    )


def teardown_module():
    bbss.stop_services(
        ["-m basic_bot.services.central_hub", "-m basic_bot.services.vision_cv2"]
    )


class TestVisionCV2:
    def test_object_detection(self):
        ws = hub.connect()
        # this name shows up in central hub logs and is helpful for debugging
        hub.send_identity(ws, "TestVisionCV2:test_object_detection")
        response = hub.recv(ws)
        assert response["type"] == "iseeu"
        hub.send_subscribe(ws, ["recognition"])

        if tc.IS_HEADLESS:
            print("Skipping object detection test in headless mode")
            return

        ws.close()
