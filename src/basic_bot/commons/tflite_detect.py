"""
This class provides object detection using Tensor Flow Lite.
"""

import numpy as np
from tflite_support.task import core
from tflite_support.task import processor
from tflite_support.task import vision

from basic_bot.commons import constants as c, log


class TFLiteDetect:
    detector = None

    # args are used for testing
    def __init__(self, model=None, use_coral_tpu=None):
        # Initialize the object detection model
        if use_coral_tpu is None:
            use_coral_tpu = c.BB_ENABLE_CORAL_TPU

        if model is None:
            if use_coral_tpu:
                # model = f"{TFLITE_DATA_DIR}/efficientdet_lite0_edgetpu.tflite"
                model = f"{c.BB_TFLITE_DATA_DIR}/{c.BB_TFLITE_MODEL_CORAL}"
            else:
                model = f"{c.BB_TFLITE_DATA_DIR}/{c.BB_TFLITE_MODEL}"

        log.info(f"TFliteDetect using model={model}, use_coral_tpu={use_coral_tpu}")

        base_options = core.BaseOptions(
            file_name=model,
            use_coral=(use_coral_tpu),
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
        results = []
        if detection_result.detections:
            for detection in detection_result.detections:
                # at some point the tensor-flow API changed from
                # classes to categories and from class_name to category_name
                categories = (
                    detection.categories
                    if hasattr(detection, "categories")
                    else detection.classes
                )
                bestClassification = max(categories, key=lambda x: x.score)
                class_name = (
                    bestClassification.category_name
                    if hasattr(bestClassification, "category_name")
                    else bestClassification.class_name
                )
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
                        "classification": class_name,
                        "confidence": bestClassification.score,
                    }
                )

        return results
