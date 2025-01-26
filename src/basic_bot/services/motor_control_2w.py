"""
    Provides motor control for a 2-wheel drive robot via the central_hub
    key: "throttles".

    Sending a state update to the central_hub, for example:
    ```json
    {
        "throttles": {
            "left": 0.5,
            "right": 0.5
        }
    }
    ```
    ...would set the left and right throttles to half ahead.  You can also set
    the throttles to negative values >= -1 to go in reverse.

    The motor control will send a state update back to the central_hub with the
    current state of the motors, for example:
    ```json
    {
        "motors": {
            "left": 0.5,
            "right": 0.5
        }
    }
    ```
"""

import time
import json
import asyncio
import traceback
import websockets
from websockets.client import WebSocketClientProtocol

from basic_bot.commons import constants as c, messages, log

if c.BB_ENV == "production":
    from adafruit_motorkit import MotorKit

    kit = MotorKit(c.BB_MOTOR_I2C_ADDRESS)
    motors = [kit.motor1, kit.motor2, kit.motor3, kit.motor4]
    left_motor = motors[c.BB_LEFT_MOTOR_CHANNEL]
    right_motor = motors[c.BB_RIGHT_MOTOR_CHANNEL]
else:
    # stub out the motor controller for testing and local (mac/windows) development
    log.info(
        "basic_bot.services.motor_control_2w not running in BB_ENV=production. Using stub motor controller"
    )

    class Motor:
        def __init__(self):
            self.throttle = 0

    left_motor = Motor()
    right_motor = Motor()


async def send_motor_state(websocket: WebSocketClientProtocol) -> None:
    await messages.send_update_state(
        websocket,
        {
            "motors": {
                "left_throttle": left_motor.throttle,
                "right_throttle": right_motor.throttle,
            }
        },
    )


async def provide_state() -> None:
    while True:
        try:
            log.info(f"connecting to {c.BB_HUB_URI}")
            async with websockets.connect(c.BB_HUB_URI) as websocket:
                # reset motors incase of restart due to crash
                left_motor.throttle = 0
                right_motor.throttle = 0

                await messages.send_identity(websocket, "motor_control_2w")
                await messages.send_subscribe(websocket, ["throttles"])
                async for message in websocket:
                    if c.BB_LOG_ALL_MESSAGES:  # log all messages except pongs
                        log.info(f"received from central hub:  {message}")

                    data = json.loads(message)
                    message_data = data.get("data")
                    if "throttles" in message_data:
                        left_throttle = min(
                            max(message_data["throttles"]["left"], -1), 1
                        )
                        right_throttle = min(
                            max(message_data["throttles"]["right"], -1), 1
                        )
                        log.info(
                            f"setting throttles ({left_throttle}, {right_throttle})"
                        )
                        left_motor.throttle = left_throttle
                        right_motor.throttle = right_throttle
                        await send_motor_state(websocket)

                await asyncio.sleep(0.05)

        except:
            traceback.print_exc()

        print("socket disconnected.  Reconnecting in 5 sec.BB_..")
        time.sleep(5)


def main() -> None:
    asyncio.run(provide_state())


if __name__ == "__main__":
    main()
