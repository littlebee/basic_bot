#!/usr/bin/env python3
"""

   Simple http server for serving the react web app from build dir

"""

import os
import threading
import logging

import psutil

from flask import Flask, send_from_directory, Response
from flask_cors import CORS

from basic_bot.commons import web_utils, log, constants as c
from basic_bot.commons.hub_state import HubState
from basic_bot.commons.hub_state_monitor import HubStateMonitor

hub_state = HubState()

app = Flask(__name__, static_url_path="/static")
CORS(app, supports_credentials=True)

monitor = HubStateMonitor(hub_state, "webserver", "*")
monitor.start()

dir_path = os.path.join(os.getcwd(), c.BB_WEB_PUBLIC)
log.info(f"serving from dir_path: {dir_path}")


@app.route("/stats")
def send_stats() -> Response:
    (cpu_temp, *rest) = [
        int(i) / 1000
        for i in os.popen("cat /sys/devices/virtual/thermal/thermal_zone*/temp")
        .read()
        .split()
    ]
    return web_utils.json_response(
        app,
        {
            "system": {
                "cpuPercent": psutil.cpu_percent(),
                "ram": psutil.virtual_memory()[2],
                "temp": {
                    "CPU": cpu_temp,
                },
            },
        },
    )


@app.route("/state")
def send_state() -> Response:
    return web_utils.json_response(app, hub_state.state)


@app.route("/<path:filename>")
def send_file(filename: str) -> Response:
    return send_from_directory(dir_path, filename)


@app.route("/static/js/<path:path>")
def send_static_js(path: str) -> Response:
    return send_from_directory(dir_path + "/static/js", path)


@app.route("/static/css/<path:path>")
def send_static_css(path: str) -> Response:
    return send_from_directory(dir_path + "/static/css", path)


@app.route("/")
def index() -> Response:
    return send_from_directory(dir_path, "index.html")


class webapp:
    def __init__(self) -> None:
        pass

    def thread(self) -> None:
        app.run(host="0.0.0.0", port=80, threaded=True)

    def start_thread(self) -> None:
        thread = threading.Thread(target=self.thread)
        # 'True' means it is a front thread,it would close when the mainloop() closes
        thread.setDaemon(False)
        thread.start()  # Thread starts


def start_app() -> None:
    logger = logging.getLogger(__name__)
    logger.info(f"webapp started. serving {dir_path}")

    flask_app = webapp()
    flask_app.start_thread()


if __name__ == "__main__":
    start_app()
