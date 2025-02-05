import os
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite  # type: ignore

from typing import Optional, List, Dict, Any

from basic_bot.commons import constants as c, log
from basic_bot.commons.coco_lables import coco_lables as labels


class TFLiteDetect:
    """
    This class provides object detection using Tensor Flow Lite.
    """

    # args are used for testing
    def __init__(
        self, model: Optional[str] = None, use_coral_tpu: Optional[bool] = None
    ) -> None:
        """
        Constructor

        Args:

        - model: the path to the tflite model file
        - use_coral_tpu: whether to use the Coral TPU for inference
        """
        # Initialize the object detection model
        if use_coral_tpu is None:
            use_coral_tpu = c.BB_ENABLE_CORAL_TPU

        if model is None:
            if use_coral_tpu:
                model = c.BB_TFLITE_MODEL_CORAL
            else:
                model = c.BB_TFLITE_MODEL

        if model.startswith("./"):
            model = os.path.join(os.path.dirname(__file__), model[2:])

        log.info(f"TFliteDetect using model={model}, use_coral_tpu={use_coral_tpu}")

        # Load TFLite model and allocate tensors.
        self.interpreter = tflite.Interpreter(model_path=model, num_threads=4)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.height = self.input_details[0]["shape"][1]
        self.width = self.input_details[0]["shape"][2]
        self.floating_model = False
        if self.input_details[0]["dtype"] == np.float32:
            self.floating_model = True

    def get_prediction(self, img: Any) -> List[Dict[str, Any]]:
        """
        Given an image array, return a list of detected objects.

        Each detected object is a dictionary with the following:

        - boundingBox: [x1, y1, x2, y2]
        - classification: string
        - confidence: float (0-1)

        """
        initial_h, initial_w, channels = img.shape
        frame = cv2.resize(img, (self.width, self.height))

        input_data = np.expand_dims(frame, axis=0)
        if self.floating_model:
            input_data = (np.float32(input_data) - 127.5) / 127.5  # type: ignore
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)

        log.debug("Running inference...")
        self.interpreter.invoke()
        detected_boxes = self.interpreter.get_tensor(self.output_details[0]["index"])
        detected_classes = self.interpreter.get_tensor(self.output_details[1]["index"])
        detected_scores = self.interpreter.get_tensor(self.output_details[2]["index"])
        num_boxes = self.interpreter.get_tensor(self.output_details[3]["index"])

        results = []
        for i in range(int(num_boxes)):
            top, left, bottom, right = detected_boxes[0][i]
            classId = int(detected_classes[0][i])
            score = detected_scores[0][i]
            if score > c.BB_OBJECT_DETECTION_THRESHOLD:
                xmin = left * initial_w
                ymin = top * initial_h
                xmax = right * initial_w
                ymax = bottom * initial_h
                box = [float(xmin), float(ymin), float(xmax), float(ymax)]
                class_name = labels[classId]
                results.append(
                    {
                        "boundingBox": box,
                        "classification": class_name,
                        "confidence": score,
                    }
                )
        log.debug(f"tflite_detect results: {results}")
        return results
