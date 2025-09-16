"""
    Provides a service to control the servo motors using the PCA9685 PWM driver.

    On startup, this service will look for a file named `servo_config.yml` in the
    directory where the service was started which should always be the root project
    dir of your basic_bot project. This file should contain a list of servos with
    the following format:

    ```yaml
    servos:
      - name: servo_name
        channel: 0
        motor_range: 180
        min_angle: 0
        max_angle: 180
        min_pulse: 500
        max_pulse: 2500
    ```

    If you update the `servo_config.yml` file, you will need to restart the service.

    The 'name' and 'channel' are required for each servo.  The example above shows
    the default values for the other parameters.

    - `name` (required) is the unique name of the servo.
    - `channel` (required) is the channel on the PCA9685 board that the servo is connected to.
    - `motor_range` is the total manufacturer's range of the servo in degrees.
    - `min_angle` and `max_angle` are the minimum and maximum angles that the servo should
       be constrained.
    - `min_pulse` and `max_pulse` are the minimum and maximum pulse widths in microseconds
       that the servo will accept as specified by the manufacturer.

    The service listens for messages on the central_hub key: "servo_angles". The
    message `data` should be a dictionary with keys that are the servo `names`
    from `servo_config.yml` and values that are the desired angle in degrees.

    ```json
    {
        "servo_angles": {
            "servo_name": 90
        }
    }
    ```

    The service will send a state update back to the central_hub with the current
    state of the servos using the key "servo_current_angles", for example:
    ```json
    {
        "servo_actual_angles": {
            "servo_name": 90
        }
    }
    ```

    The service will also provide the current servo config as read from `servo_config.yml`
    at service startup using the key "servo_config", for example:
    ```json
    {
        "servo_config": {
            "servos": [
                {
                    "name": "servo_name",
                    "channel": 0,
                    "motor_range": 180,
                    "min_angle": 0,
                    "max_angle": 180,
                    "min_pulse": 500,
                    "max_pulse": 2500
                }
            ]
        }
    }
    ```
"""

import asyncio
from typing import Dict, Any

from basic_bot.commons import log, messages
from websockets.client import WebSocketClientProtocol
from basic_bot.commons.servo_pca9685 import Servo
from basic_bot.commons.servo_config import read_servo_config
from basic_bot.commons.hub_state import HubState
from basic_bot.commons.hub_state_monitor import HubStateMonitor

ANGLE_UPDATE_FREQUENCY = 0.1  # seconds = 10Hz

servos_config = read_servo_config()["servos"]
log.info(f"Initializing {len(servos_config)} servos...")
servos_by_name = {
    # channel and name are validated as required
    servo["name"]: Servo(servo)
    for servo in servos_config
}
log.info(f"Servos initialized: {servos_by_name}")

hub_state = HubState(
    {
        "servo_config": {"servos": servos_config},
        "servo_actual_angles": {
            name: servo.current_angle for name, servo in servos_by_name.items()
        },
    }
)


async def send_servo_config(websocket: WebSocketClientProtocol) -> None:
    # read config from the Servo objects instead of the file for
    # testing mostly,  Just giving back the config we read from the file
    # is disingenuous and doesn't tell us if the Servo object has the data
    # as expected.
    servos_config = [
        {
            "name": servo.name,
            "channel": servo.channel,
            "motor_range": servo.motor_range,
            "min_angle": servo.min_angle,
            "max_angle": servo.max_angle,
            "min_pulse": servo.min_pulse,
            "max_pulse": servo.max_pulse,
        }
        for servo in servos_by_name.values()
    ]

    await messages.send_update_state(
        websocket, {"servo_config": {"servos": servos_config}}
    )


last_servo_angles: dict[str, Any] = {}


async def send_servo_angles(websocket: WebSocketClientProtocol, force: bool = False) -> None:
    global last_servo_angles

    angles = {name: servo.current_angle for name, servo in servos_by_name.items()}
    if not force and angles == last_servo_angles:
        return

    last_servo_angles = angles
    await messages.send_update_state(
        websocket,
        {"servo_actual_angles": angles},
    )


async def update_servo_angles(websocket: WebSocketClientProtocol) -> None:
    while True:
        await send_servo_angles(websocket)
        await asyncio.sleep(ANGLE_UPDATE_FREQUENCY)


def handle_connect(websocket: WebSocketClientProtocol) -> None:
    # if we disconnect and reconnect we need to resend the current state
    log.info("connected to central hub")
    asyncio.create_task(send_servo_config(websocket))
    # need to force send the current angles to the central hub on reconnect
    # in case it was restarted and lost the state
    asyncio.create_task(send_servo_angles(websocket, force=True))
    asyncio.create_task(update_servo_angles(websocket))


def handle_state_update(_websocket: WebSocketClientProtocol, _msg_type: str, msg_data: Dict[str, Any]) -> None:
    angles = msg_data.get("servo_angles")
    log.debug(f"received servo_angles: {angles}")
    if angles:
        for name, angle in angles.items():
            log.debug(f"moving {name} to {angle}")
            servos_by_name[name].move_to(angle)


hub_monitor = HubStateMonitor(
    hub_state,
    # identity of the service
    "servo_control",
    # keys to subscribe to
    ["servo_angles"],
    # callback function to call when a message is received
    # Note that when started using bb_start, any standard output or error
    # will be captured and logged to the ./logs directory.
    on_state_update=handle_state_update,
    on_connect=handle_connect,
)
hub_monitor.start()
