---
title: central_hub
---
<a id="basic_bot.services.central_hub"></a>

# basic\_bot.services.central\_hub

Provides an ultra-light pub/sub service with < 10ms latecy over
websockets.  The state of published keys is maintained in memory.

This python process is meant to be run as a service by basic_bot.

You can also run it in the foreground for debugging purposes.  ex:
```sh
python3 -m basic_bot.services.central_hub
```

Central hub is also the publisher of several state keys:
```json
{
    "hub_stats": {
        "state_updates_recv": 0
    },
    "subsystem_stats": {}
}
```

