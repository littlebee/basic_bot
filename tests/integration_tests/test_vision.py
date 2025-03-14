# skip this test if tflite_runtime is not installed
import basic_bot.test_helpers.skip_unless_tflite_runtime  # noqa: F401

import cv2
import requests
import time
from pathlib import Path

import basic_bot.test_helpers.central_hub as hub
import basic_bot.test_helpers.start_stop as sst
import basic_bot.commons.constants as c

# this also test all of the commons.vision_client.py functions
import basic_bot.commons.vision_client as vision_client


def setup_module():
    sst.start_service("central_hub", "python -m basic_bot.services.central_hub")
    sst.start_service("vision", "python -m basic_bot.services.vision")


def teardown_module():
    sst.stop_service("central_hub")
    sst.stop_service("vision")


class TestVisionCV2:
    def test_object_detection(self):
        ws = hub.connect()
        # this name shows up in central hub logs and is helpful for debugging
        hub.send_identity(ws, "TestVisionCV2:test_object_detection")
        response = hub.recv(ws)
        assert response["type"] == "iseeu"
        hub.send_subscribe(ws, ["recognition"])

        # The service has been started and it should be running
        # in test mode (BB_ENV=test) which causes services/vision.py to import and use
        # the test_helpers/camera_mock and should be pumping out frames at 60fps
        # using mock camera that are 50% images with pets.
        pet_count = 0
        not_pet_count = 0
        for i in range(100):
            response = hub.recv(ws)
            assert response["type"] == "stateUpdate"
            objects = response["data"]["recognition"]
            found_pet = False
            for obj in objects:
                if obj["classification"] in ["cat", "dog"]:
                    found_pet = True
                    break

            if found_pet:
                pet_count += 1
            else:
                not_pet_count += 1

        assert pet_count > 0

        pet_ratio = pet_count / (pet_count + not_pet_count)

        # TODO: not sure why this need to be +/- 0.19, but it seems
        # to be the case on CD/CD runner.  Its possible that because
        # the camera_mock is pushing out 60fps, the ratio is dependent
        # on the stride of tflite_detect.py which is running at 25-30fps
        assert 0.47 < pet_ratio < 0.53

        ws.close()

    def test_vision_stats(self):
        """
        Test the /stats http endpoint of the vision service which
        should be up and running on port c.BB_VISION_PORT
        """
        url = f"http://localhost:{c.BB_VISION_PORT}/stats"
        response = requests.get(url)
        assert response.status_code == 200

        response_data = response.json()

        # i'm reluctant to assert much about the stats because
        # they might be brittle and change with the machine running
        # the tests
        assert "capture" in response_data
        assert "recognition" in response_data

        """
        this is kinda cool to see the stats in the test output run
        this test like this:
        ```sh
        pyttest -vv -s tests/integration_tests/test_vision.py
        ```
        to see the output of the print below...
        """

        print(response_data)

        """
        this is what the output looks like on a pi 5:
        ```
        PASSED
        tests/integration_tests/test_vision.py::TestVisionCV2::test_vision_stats
        {'capture': {'totalFramesRead': 218, 'totalTime': 3.8893659114837646,
            'overallFps': 56.05026756580859, 'fpsStartedAt': 1739037182.7373936, 'floatingFps': 0.0},
        'recognition': {
            'last_objects_seen': [{'bounding_box': [36.80461883544922, 16.702866554260254, 635.1525497436523, 481.2730407714844], 'classification': 'person', 'confidence': 0.69140625}],
            'fps': {
                'totalFramesRead': 119, 'totalTime': 3.8534364700317383,
                'overallFps': 30.88152637923725, 'fpsStartedAt': 1739037182.773333, 'floatingFps': 0.0}, 'total_objects_detected': 181, 'last_frame_duration': 0.030310392379760742}}
        ```
        This is with a camera capturing at ~60fps (camera_mock) and tflite
        detection is running at ~30fps!  That's kinda outstanding. Scatbot
        needed the Coral TPU to get to 28fps inference on the pi 4.
        """

    def test_record_video(self):
        TEST_DURATION = 3.5

        vidfile_count_before = len(list(Path(c.BB_VIDEO_PATH).glob("*.mp4")))
        imgfile_count_before = len(list(Path(c.BB_VIDEO_PATH).glob("*.jpg")))

        # test that video can be recorded
        response = vision_client.send_record_video_request(TEST_DURATION)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Test that the service will only record one video at a time and return
        # not ok if a second request is made while the first is still recording
        response = vision_client.send_record_video_request(TEST_DURATION)
        assert response.json()["status"] == 304

        # The video recording is started async. Recording, reencoding the video,
        # and generating the thumbnail (mostly reencoding) takes a few seconds
        time.sleep(TEST_DURATION * 2)

        vidfile_count_after = len(list(Path(c.BB_VIDEO_PATH).glob("*.mp4")))
        assert (
            vidfile_count_after == vidfile_count_before + 1
        ), "should have created exactly one video file"

        imgfile_count_after = len(list(Path(c.BB_VIDEO_PATH).glob("*.jpg")))
        assert (
            imgfile_count_after == imgfile_count_before + 1
        ), "should have created exactly one image file"

        # tests video list retrieval
        response = vision_client.fetch_recorded_videos()
        assert response.status_code == 200
        jsonResp = response.json()
        assert_is_array_of_strings(jsonResp)
        assert len(jsonResp) == vidfile_count_after

        # test individual video retrieval
        vid_file_name = jsonResp[0] + ".mp4"
        response = vision_client.fetch_recorded_video(vid_file_name)
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "video/mp4"

        url = f"{c.BB_VISION_URI}/recorded_video/{vid_file_name}"
        assert_video_duration(url, TEST_DURATION)

        # test thumbnail retrieval
        img_file_name = jsonResp[0] + ".jpg"
        response = vision_client.fetch_recorded_video(img_file_name)
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/jpeg"


def assert_is_array_of_strings(obj):
    assert isinstance(obj, list), "Input is not a list"
    assert all(
        isinstance(item, str) for item in obj
    ), "Not all elements in the list are strings"


def assert_video_duration(url, expected_duration):
    TOLERANCE = 0.1  # seconds of tolerance for video duration test

    data = cv2.VideoCapture(url)
    frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = data.get(cv2.CAP_PROP_FPS)
    duration = frames / fps
    data.release()
    assert expected_duration - TOLERANCE < duration < expected_duration + TOLERANCE
