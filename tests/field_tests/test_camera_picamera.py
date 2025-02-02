import os
import socket
import cv2

from basic_bot.commons.camera_picamera import CameraPiCamera


def test_single_frame_capture():
    camera = CameraPiCamera()
    frame = camera.get_frame()

    ret = cv2.imwrite("opencv-test-output.jpg", frame)
    if ret:
        print("Successfully saved")
    else:
        print(f"Something went wrong.  ret from imwrite: {ret}")

    assert ret

    return ret


if __name__ == "__main__":

    ret = test_single_frame_capture()
    if ret:
        print(
            "Successfully saved. You can scp the file to your local machine with something like:"
        )
        print(
            f"scp pi@{socket.gethostname()}.local:{os.getcwd()}/opencv-test-output.jpg ."
        )
