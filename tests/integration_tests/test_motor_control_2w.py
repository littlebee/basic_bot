import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as bbss


def setup_module():
    bbss.start_services(
        ["-m basic_bot.services.central_hub", "-m basic_bot.services.motor_control_2w"]
    )


def teardown_module():
    bbss.stop_services(
        ["-m basic_bot.services.central_hub", "-m basic_bot.services.motor_control_2w"]
    )


class TestMotorControl2w:
    def test_set_throttles(self):
        ws = hub.connect()
        # this name shows up in central hub logs and is helpful for debugging
        hub.send_identity(ws, "TestMotorControl2w-test_set_throttles")
        response = hub.recv(ws)
        assert response["type"] == "iseeu"

        hub.send_subscribe(ws, ["motors"])

        test_throttles = [
            {"left": 0.5, "right": 0.5},
            {"left": 0.0, "right": 0.0},
            {"left": -0.5, "right": -0.5},
            {"left": 0.0, "right": 0.0},
        ]

        for throttle in test_throttles:
            hub.send_update_state(ws, {"throttles": throttle})
            response = hub.recv(ws)
            print(f"for {throttle=}, {response=}")
            assert response["data"]["motors"]["left_throttle"] == throttle["left"]
            assert response["data"]["motors"]["right_throttle"] == throttle["right"]

        limit_tests = [
            {"test": {"left": 0, "right": 0}, "expected": {"left": 0, "right": 0}},
            {
                "test": {"left": -2.0, "right": -2.0},
                "expected": {"left": -1.0, "right": -1.0},
            },
            {
                "test": {"left": 1.1, "right": 1.000001},
                "expected": {"left": 1.0, "right": 1.0},
            },
            {
                "test": {"left": -1.1, "right": -1.00001},
                "expected": {"left": -1.0, "right": -1.0},
            },
        ]

        for test in limit_tests:
            hub.send_update_state(ws, {"throttles": test["test"]})
            response = hub.recv(ws)
            print(f"for {test=}, {response=}")
            assert (
                response["data"]["motors"]["left_throttle"] == test["expected"]["left"]
            )
            assert (
                response["data"]["motors"]["right_throttle"]
                == test["expected"]["right"]
            )

        ws.close()
