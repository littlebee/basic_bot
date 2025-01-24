#!/usr/bin/env python3
"""

   Simple service service example that just sets sets a state key value,
   sleeps for a while prints the current local state and then sleeps for a while.

"""
import asyncio
from basic_bot.commons import log
from basic_bot.commons.hub_state import HubState
from basic_bot.commons.hub_state_monitor import HubStateMonitor
import basic_bot.commons.messages as bb_message


# HubState is a class that manages the process local copy of the state.
# Each service runs as a process and  has its own partial or full instance
# of HubState.
hub_state = HubState({"worthless_counter": -999})

# HubStateMonitor will open a websocket connection to the central hub
# and start a thread to listen for state changes.  The monitor will call,
# on the callback function with the new state before applying the changes to
# the local state.
hub_monitor = HubStateMonitor(
    hub_state,
    # identity of the service
    "my_service",
    # keys to subscribe to
    ["worthless_counter", "subsystem_stats"],
    # callback function to call when a message is received
    # Note that when started using bb_start, any standard output or error
    # will be captured and logged to the ./logs directory.
    on_state_update=lambda websocket, msg_type, msg_data: print(
        f"on_message_recv: {msg_type=}, {msg_data=}"
    ),
)
hub_monitor.start()


async def main():
    log.info("in my_service:main()")
    i = 0
    while True:
        """
        Replace this with your service logic that either responds
        to state changes or sends state updates to the central hub
        based on external data like that from motors or sensors
        """
        i += 1
        log.info(f"maybe sending state update {hub_monitor.connected_socket}")
        if hub_monitor.connected_socket:
            await bb_message.send_state_update(
                hub_monitor.connected_socket, {"worthless_counter": i}
            )
        await asyncio.sleep(1)
        log.info(f"my_service state: {hub_state.state}")


log.info("starting my_service via asyncio")
asyncio.run(main())
