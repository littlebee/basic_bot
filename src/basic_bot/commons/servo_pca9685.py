#!/usr/bin/env python3

import sys
import time
import threading
import traceback
from typing import Optional

from basic_bot.commons import log, env, constants as c
from basic_bot.commons.servo_config import ServoOptions, ServoOptionsDefaults

if c.BB_ENV == "production":
    from board import SCL, SDA  # type: ignore
    import busio  # type: ignore

    # Import the PCA9685 module. Available in the bundle and here:
    #   https://github.com/adafruit/Adafruit_CircuitPython_PCA9685
    from adafruit_pca9685 import PCA9685  # type: ignore
    from adafruit_motor import servo as servo_af  # type: ignore

    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c)
    pca.frequency = 50

else:
    log.info(f"commons.Servo running in {c.BB_ENV} mode.  Using mock servo libs")

    class pca:  # type: ignore
        channels = [i for i in range(16)]

    class servo_af:  # type: ignore
        class Servo:
            def __init__(self, channel: int, min_pulse: int = 500, max_pulse: int = 2500) -> None:
                self.channel = channel
                self.min_pulse = min_pulse
                self.max_pulse = max_pulse
                self.fraction: float = 0.0


# env var to turn on console debug output
DEBUG_MOTORS = env.env_bool("DEBUG_MOTORS", False)

# how many deg to turn per step (abs)
STEP_DEGREES = 1
# how long to wait between steps (default; use step_delay setter to change at run time)
DEFAULT_STEP_DELAY = 0.0001

# the precision of the servo motors in degrees
SERVO_PRECISION = 0.5


def limit_angle(angle: float, min_angle: float, max_angle: float) -> float:
    limited_angle = angle
    if angle < min_angle:
        limited_angle = min_angle
    elif angle > max_angle:
        limited_angle = max_angle

    return limited_angle


class Servo:
    """
    This class controls a single servo motor using the Adafruit PCA9685 servo controller.
    It uses a background thread to move the motor to a destination angle at a give
    fraction of the motor's range and thereby control the speed.

    It requires the following Adafruit CircuitPython libraries to be installed:
    ```sh
    python -m pip install adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motorkit
    ```
    """

    def __init__(
        self,
        servo_options: ServoOptions,
    ) -> None:
        """Constructor"""
        # background thread that steps motor to destination
        self.thread: Optional[threading.Thread] = None

        self.pause_event = threading.Event()
        self.stopped_event = threading.Event()
        self.force_stop = False
        self._step_delay = DEFAULT_STEP_DELAY

        self.name: str = servo_options["name"]
        self.channel: int = servo_options["channel"]
        self.motor_range: int = (
            servo_options.get("motor_range") or ServoOptionsDefaults.motor_range
        )
        self.min_pulse: int = (
            servo_options.get("min_pulse") or ServoOptionsDefaults.min_pulse
        )
        self.max_pulse: int = (
            servo_options.get("max_pulse") or ServoOptionsDefaults.max_pulse
        )
        self.min_angle: int = (
            servo_options.get("min_angle") or ServoOptionsDefaults.min_angle
        )
        self.max_angle: int = (
            servo_options.get("max_angle") or ServoOptionsDefaults.max_angle
        )
        self.mid_angle: float = (
            float(self.min_angle) + float(self.max_angle - self.min_angle) / 2
        )

        self.destination_angle = self.mid_angle

        self.servo = servo_af.Servo(
            pca.channels[self.channel],
            min_pulse=self.min_pulse,
            max_pulse=self.max_pulse,
        )
        # we need to initialize the servo to the middle of the range
        # to know where it actually is
        log.info(
            f"initializing servo {self.channel} to mid range {self.mid_angle} deg of {self.motor_range} deg motor range"
        )
        self.servo.fraction = self.destination_angle / self.motor_range

        self.thread = threading.Thread(target=self._thread)
        self.thread.start()

    @property
    def current_angle(self) -> float:
        """Returns the current angle of the servo motor"""
        try:
            fraction: float = float(self.servo.fraction)
            return fraction * self.motor_range
        except OSError as error:
            # Was getting intermittent exception from adafruit servo kit
            # originating from i2c_bus.read_i2c_block_data()
            log.error(f"OSError caught in current_angle: {error}\n")
            # just pretend we are at the destination (stop moving) and carry on
            return self.destination_angle

    @property
    def step_delay(self) -> float:
        """Returns the current step delay"""
        return self._step_delay

    @step_delay.setter
    def step_delay(self, value: float) -> None:
        """Sets the step delay"""
        self._step_delay = value

    def move_to(self, angle: float) -> None:
        """Move the servo to the specified angle"""
        new_angle = limit_angle(angle, self.min_angle, self.max_angle)
        if DEBUG_MOTORS:
            log.info(
                f"move_to {self.channel}, {self.current_angle}, {angle}, {self.destination_angle}, {self.min_angle}, {self.max_angle}"
            )

        if abs(self.destination_angle - new_angle) < SERVO_PRECISION:
            if DEBUG_MOTORS:
                log.info(
                    f"{self.current_angle} already at destination angle {self.destination_angle}"
                )
            return

        self.destination_angle = new_angle
        self.stopped_event.clear()
        self.resume()

    def pause(self) -> None:
        """Pause the servo movement"""
        self.pause_event.clear()

    def resume(self) -> None:
        """Resume the servo movement"""
        self.pause_event.set()

    def stop_thread(self) -> None:
        """Stop the servo movement thread"""
        self.stopped_event.set()
        self.force_stop = True
        # thread could be waiting on pause_event, resume to quit
        self.resume()

    def wait_for_motor_stopped(self) -> None:
        """Wait for the motor to stop moving"""
        if DEBUG_MOTORS:
            log.info(f"waiting on stopped event on channel {self.channel}")
        self.stopped_event.wait()
        if DEBUG_MOTORS:
            log.info(f"after wait: {self.channel} {self.stopped_event.is_set()}")

    def _thread(self) -> None:
        log.info(f"Starting servo movement thread. {self.current_angle}")
        self.started_at = time.time()

        if DEBUG_MOTORS:
            log.info(
                f"initializing motor {self.channel} to {self.destination_angle}deg"
            )
        self.servo.fraction = self.destination_angle / self.motor_range
        time.sleep(0.5)
        # need to establish initial position of motor

        # start running
        self.pause_event.set()
        while not self.force_stop:
            self.pause_event.wait()
            direction = 1
            if self.current_angle > self.destination_angle:
                direction = -1

            if DEBUG_MOTORS:
                log.info(
                    f"servo.py thread loop: channel={self.channel} direction={direction} {self.current_angle} {self.destination_angle} "
                )
            if not self._step_move(direction):
                if DEBUG_MOTORS:
                    log.info(f"setting stopped event on channel={self.channel}")
                self.stopped_event.set()
                self.pause_event.clear()

        log.info("servo thread exit on channel={self.channel}")

    def _step_move(self, direction: int) -> bool:
        """direction = -1 = left; 1 = right.  returns true if did move"""
        try:
            would_overshoot = self._step_would_overshoot_dest(direction)
            if DEBUG_MOTORS:
                log.info(
                    f"stepping channel={self.channel}, {direction}, {self.current_angle}, {self.destination_angle}, {would_overshoot}"
                )

            if self.current_angle == self.destination_angle:
                return False

            if would_overshoot:
                # get the servo as close to the destination as possible
                self.servo.fraction = self.destination_angle / self.motor_range
                # and then stop the movement loop
                return False

            new_angle = self.current_angle + (STEP_DEGREES * direction)

            self.servo.fraction = new_angle / self.motor_range
            time.sleep(self._step_delay)

            return True
        except Exception:
            log.error(
                f"Exception caught in _step_move for channel={self.channel}: {traceback.format_exc()}"
            )
            return False

    def _step_would_overshoot_dest(self, direction: int) -> bool:
        current_angle = self.current_angle
        new_angle = current_angle + STEP_DEGREES * direction
        return (direction == -1 and new_angle < self.destination_angle) or (
            direction == 1 and new_angle > self.destination_angle
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage:  servo.py <channel> (<angle>)")
        exit(1)

    channel = int(sys.argv[1])
    log.info("Ctrl+c to quit")
    test_angles = [
        0,
        180,
    ]
    log.info(f"initializing servo class on motor channel {channel}")
    servo = Servo(
        {
            "name": "test_servo",
            "channel": channel,
            "motor_range": ServoOptionsDefaults.motor_range,
            "min_angle": ServoOptionsDefaults.min_angle,
            "max_angle": ServoOptionsDefaults.max_angle,
            "min_pulse": ServoOptionsDefaults.min_pulse,
            "max_pulse": ServoOptionsDefaults.max_pulse,
        }
    )

    try:
        if len(sys.argv) > 2:
            new_angle = int(sys.argv[2])
            log.info(f"channel {channel} to {new_angle}deg")
            servo.move_to(new_angle)
            log.info("waiting for motor stopped event")
            servo.wait_for_motor_stopped()
            log.info("got stopped event.")
            servo.stop_thread()
            exit()

        else:
            while True:
                for angle in test_angles:
                    log.info(f"channel {channel} to {angle}deg")
                    servo.move_to(angle)
                    log.info("waiting for motor stopped event")
                    servo.wait_for_motor_stopped()
                    log.info("got stopped event.")
                    # log.info("got stopped event. waiting...")
                    # time.sleep(3)

    except KeyboardInterrupt:
        servo.stop_thread()
