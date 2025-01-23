"""
This class provides object detection using Tensor Flow Lite.
"""

from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision

from basic_bot.commons import constants as c, log


class TFLiteDetect:
    detector = None

    def __init__(self):
        # Initialize the object detection model
        model = None
        if c.BB_ENABLE_CORAL_TPU:
            # model = f"{TFLITE_DATA_DIR}/efficientdet_lite0_edgetpu.tflite"
            model = f"{c.BB_TFLITE_DATA_DIR}/{c.BB_TFLITE_MODEL_CORAL}"
        else:
            model = f"{c.BB_TFLITE_DATA_DIR}/{c.BB_TFLITE_MODEL}"

        log.info(f"using model {model}")

        base_options = core.BaseOptions(
            file_name=model,
            use_coral=(c.BB_ENABLE_CORAL_TPU),
            num_threads=c.BB_TFLITE_THREADS,
        )
        detection_options = processor.DetectionOptions(
            max_results=3, score_threshold=0.3
        )
        options = vision.ObjectDetectorOptions(
            base_options=base_options, detection_options=detection_options
        )
        self.detector = vision.ObjectDetector.create_from_options(options)

    def get_prediction(self, img):
        input_tensor = vision.TensorImage.create_from_array(img)
        detection_result = self.detector.detect(input_tensor)
        print(f"detection_result: {detection_result}")
        results = []
        if detection_result.detections:
            for detection in detection_result.detections:
                bestClassification = max(detection.classes, key=lambda x: x.score)
                results.append(
                    {
                        "boundingBox": [
                            detection.bounding_box.origin_x,
                            detection.bounding_box.origin_y,
                            detection.bounding_box.origin_x
                            + detection.bounding_box.width,
                            detection.bounding_box.origin_y
                            + detection.bounding_box.height,
                        ],
                        "classification": bestClassification.class_name,
                        "confidence": bestClassification.score,
                    }
                )

        return results
