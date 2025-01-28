---
title: motor_control_2w
---
<a id="basic_bot.services.motor_control_2w"></a>

# basic\_bot.services.motor\_control\_2w

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

