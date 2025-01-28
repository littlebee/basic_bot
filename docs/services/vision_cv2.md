---
title: vision_cv2
---
<a id="basic_bot.services.vision_cv2"></a>

# basic\_bot.services.vision\_cv2

Provide image feed and object recognition based on open-cv for the
video capture input.  This service will provide a list of objects
and their bounding boxes in the image feed via central hub.

A vision feed is provided via http://<ip>:<port>/video_feed that
can be used in an HTML 'img' element.  The image feed is a multipart
jpeg stream (for now; TODO: reassess this).  Assuming that the vision
service is running on the same host machine as the browser client
location, you can do something like:
```html
<img src="http://localhost:5001/video_feed" />
```

The following data is provided to central_hub as fast as image capture and
recognition can be done:

```json
{
    "recognition": [
        {
            "bounding_box": [x1, y1, x2, y2],
            "classification": "person",
            "confidence": 0.99
        },
        {
            "bounding_box": [x1, y1, x2, y2],
            "classification": "dog",
            "confidence": 0.75
        }
    ]
}
```
The [x1, y1, x2, y2] bounding box above is actually sent as
the numeric values of the bounding box in the image.

Origin:
    This was originally pilfered from
    https://github.com/adeept/Adeept_RaspTank/blob/a6c45e8cc7df620ad8977845eda2b839647d5a83/server/app.py

    Which looks like it was in turn pilfered from
    https://blog.miguelgrinberg.com/post/flask-video-streaming-revisited

    Thank you, @adeept and @miguelgrinberg!

<a id="basic_bot.services.vision_cv2.gen_rgb_video"></a>

#### gen\_rgb\_video

```python
def gen_rgb_video(camera: OpenCvCamera) -> Generator[bytes, None, None]
```

Video streaming generator function.

<a id="basic_bot.services.vision_cv2.video_feed"></a>

#### video\_feed

```python
@app.route("/video_feed")
def video_feed() -> Response
```

Video streaming route. Put this in the src attribute of an img tag.

