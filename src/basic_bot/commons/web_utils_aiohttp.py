"""
Utility functions for handling aiohttp web responses.
"""

import json
import os

from aiohttp import web

from basic_bot.commons import log


# TODO : maybe move these to aiohttp web utils file (modeled after commons/web_utils)
def json_response(status, data):
    """Return a JSON response using aiortc web."""
    return web.Response(
        status=status,
        content_type="application/json",
        text=json.dumps(data),
    )


def respond_ok(data=None):
    """Return a JSON response with status ok."""
    return json_response(200, {"status": "ok", "data": data})


def respond_file(path, filename, content_type=None):
    log.info(f"sending file: {filename} from {path}")
    try:
        content = open(os.path.join(path, filename), "br").read()
    except FileNotFoundError as e:
        log.info(f"Error: File not found. {e}")
        return web.Response(status=404, text="File not found")

    return web.Response(body=content, content_type=content_type)
