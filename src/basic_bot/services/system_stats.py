"""
This optional services provides system usage statistics to the central hub
under the `system_stats` key.

The information is sampled using the [psutil library](https://pypi.org/project/psutil/)
and includes:

```json
{
    "system_stats": {
        "cpu_util": psutil.cpu_percent(),
        "cpu_temp": cpu_temp,
        "ram_util": psutil.virtual_memory()[2],
        "hostname": socket.gethostname(),
    }
}
```

Add to your basic_bot.yml file to enable this service:
```yml
services:
  - name: "system_stats"
    run: "python -m basic_bot.services.system_stats"
```

"""

import asyncio
import json
import psutil
import socket
import time
import traceback
import websockets

from basic_bot.commons import constants as c, messages


def get_update_message():
    cpu_temp = -1
    try:
        # This only works on linux
        temps = psutil.sensors_temperatures()
        cpu_temp = temps["coretemp"][0].current
    except:
        pass

    return json.dumps(
        {
            "type": "updateState",
            "data": {
                "system_stats": {
                    "cpu_util": psutil.cpu_percent(),
                    "cpu_temp": cpu_temp,
                    "ram_util": psutil.virtual_memory()[2],
                    "hostname": socket.gethostname(),
                },
            },
        }
    )


async def provide_state():
    while True:
        try:
            print(f"connecting to {c.BB_HUB_URI}")
            async with websockets.connect(c.BB_HUB_URI) as websocket:
                await messages.send_identity(websocket, "system_stats")
                while True:
                    message = get_update_message()
                    await websocket.send(message)
                    await asyncio.sleep(c.BB_SYSTEM_STATS_SAMPLE_INTERVAL)
        except:
            traceback.print_exc()

        print("socket disconnected.  Reconnecting in 5 sec...")
        time.sleep(5)


def start_provider():
    asyncio.run(provide_state())


if __name__ == "__main__":
    start_provider()
