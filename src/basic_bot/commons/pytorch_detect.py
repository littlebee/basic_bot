"""
This class objects in frames it gets from the camera object passed to
the constructor.

A thread is created that does the heavy lifting of detecting objects and updates
a class var that contains the last faces detected. This allows the thread providing
the video feed to stream at 30fps while face frames lag behind at 3fps (maybe upto 10?)
"""

"""
See [issue #1](https://github.com/littlebee/scatbot-edge-ai-shootout/issues/1)
about support for pytorch
"""

# import torchvision.transforms as T
# import torchvision

# from basic_bot.commons import constants as c


# class PytorchDetect:
#     model = None
#     transform = None

#     def __init__(self):
#         self.model = torchvision.models.detection.fasterrcnn_mobilenet_v3_large_320_fpn(
#             pretrained=True
#         )
#         self.model.eval()
#         self.transform = T.Compose([T.ToTensor()])

#     def get_prediction(self, img):
#         img = self.transform(img)
#         pred = self.model([img])
#         pred_class = [
#             c.BB_COCO_INSTANCE_CATEGORY_NAMES[i]
#             for i in list(pred[0]["labels"].numpy())
#         ]
#         pred_boxes = [
#             [(i[0], i[1]), (i[2], i[3])]
#             for i in list(pred[0]["boxes"].detach().numpy())
#         ]
#         pred_scores = list(pred[0]["scores"].detach().numpy())
#         results = []

#         indexes = range(len(pred_scores))
#         for i in indexes:
#             score = float(pred_scores[i])
#             if score > c.BB_OBJECT_DETECTION_THRESHOLD:
#                 results.append(
#                     {
#                         "bounding_box": [
#                             int(pred_boxes[i][0][0]),
#                             int(pred_boxes[i][0][1]),
#                             int(pred_boxes[i][1][0]),
#                             int(pred_boxes[i][1][1]),
#                         ],
#                         "classification": pred_class[i],
#                         "confidence": score,
#                     }
#                 )

#         return results
