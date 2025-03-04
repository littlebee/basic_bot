import time

import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as sst

from basic_bot.commons.servo_config import read_servo_config, ServoOptionsDefaults

# See also the servo_config.yml file in the root project directory.

EXPECTED_SERVO_CONFIG = {
    "servos": [
        {
            "name": servo["name"],
            "channel": servo["channel"],
            "motor_range": servo.get("motor_range") or ServoOptionsDefaults.motor_range,
            "min_angle": servo.get("min_angle") or ServoOptionsDefaults.min_angle,
            "max_angle": servo.get("max_angle") or ServoOptionsDefaults.max_angle,
            "min_pulse": servo.get("min_pulse") or ServoOptionsDefaults.min_pulse,
            "max_pulse": servo.get("max_pulse") or ServoOptionsDefaults.max_pulse,
        }
        for servo in read_servo_config()["servos"]
    ]
}


def setup_module():
    sst.start_service("central_hub", "python -m basic_bot.services.central_hub")
    sst.start_service(
        "servo_control", "python -m basic_bot.services.servo_control_pca9685"
    )


def teardown_module():
    sst.stop_service("central_hub")
    sst.stop_service("servo_control")


class TestServoControl:
    """
    Tests the servo control service.  This is was written initially to test
    the first servo control that worked with the PCA9685.  This test should work
    with any servo control service that uses the same hub keys with the same
    purpose.
    """

    def test_servo_config(self):
        ws = hub.connect()
        # this name shows up in central hub logs and is helpful for debugging
        hub.send_identity(ws, "TestServoControl-test_servo_control")
        response = hub.recv(ws)
        assert response["type"] == "iseeu"

        # The service has been started and it should be running and it also
        # should have published the servo_config key
        hub.send_get_state(ws, ["servo_config"])
        response = hub.recv(ws)
        # the expected servo config is in the servo_config.yml file + defaults
        # which the servo service publishes when it starts.
        assert response["data"]["servo_config"] == EXPECTED_SERVO_CONFIG

    def test_angles_change(self):
        test_angles = {"servo_0": 40, "servo_1": 140, "servo_2": 90}

        ws = hub.connect("test_angles_change")
        hub.send_subscribe(ws, ["servo_actual_angles"])
        hub.send_get_state(ws, ["servo_actual_angles"])
        initial_state = hub.recv(ws)
        print(f"{initial_state=}")

        hub.send_update_state(ws, {"servo_angles": test_angles})

        # it should respond within 100ms with a servo_actual_angles update
        print("waiting for current_angles update")
        updated_state = hub.recv(ws)
        print(f"Received updated state: {updated_state=}")
        assert (
            updated_state["data"]["servo_actual_angles"]
            != initial_state["data"]["servo_actual_angles"]
        )

        ws.close()

    def test_clamped_angles_change(self):
        test_angles = {"servo_0": -40, "servo_1": 55, "servo_2": 180}
        # these are based on servo_config.yml in the basic bot root project directory
        expected_clamped_angles = {"servo_0": 0, "servo_1": 55, "servo_2": 160}

        ws = hub.connect()
        hub.send_subscribe(ws, ["servo_actual_angles"])
        hub.send(ws, {"type": "getState"})
        initial_state = hub.recv(ws)
        print(f"{initial_state=}")

        # send a set_angles update to the strongarm
        hub.send_update_state(ws, {"servo_angles": test_angles})

        print("waiting for current_angle updates")

        # it should start responding within 0.1s with current_angle updates
        actual_angles = {}
        while True:
            time.sleep(0.1)
            received_state = hub.has_received_data(ws)
            if received_state is None:
                break
            print(f"{received_state=}")
            # this will throw a KeyError if the key is not present.  The only
            # service running is the servo control service and the only thing
            # it should be sending at this point is servo_actual_angles
            actual_angles = received_state["data"]["servo_actual_angles"]

        assert actual_angles == expected_clamped_angles
        ws.close()

    def test_central_hub_restarted(self):
        ws = hub.connect("test_central_hub_restarted.1")
        hub.send_get_state(ws, ["servo_actual_angles"])
        initial_state = hub.recv(ws)
        print(f"{initial_state=}")
        ws.close()

        sst.stop_service("central_hub")
        time.sleep(0.5)
        sst.start_service("central_hub", "python -m basic_bot.services.central_hub")
        time.sleep(0.5)

        # in BB_ENV=test mode, the hub state monitor used by servo_control_pca9685
        # will auto reconnect to central hub after 1 second of it going down. On
        # reconnect the servo service should send it's state (servo_actual_angles) to
        # the central hub

        ws = hub.connect("test_central_hub_restarted.2")
        hub.send_get_state(ws, ["servo_actual_angles"])
        after_state = hub.recv(ws)
        print(f"{after_state=}")
        assert (
            initial_state["data"]["servo_actual_angles"]
            == after_state["data"]["servo_actual_angles"]
        )
        ws.close()
