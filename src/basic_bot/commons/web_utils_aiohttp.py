"""
Utility functions for handling aiohttp web responses.
"""

import json
import os

from typing import Any, Optional
from aiohttp import web
from aiohttp.abc import AbstractAccessLogger
from aiohttp.web_request import BaseRequest
from aiohttp.web_response import Response, StreamResponse


from basic_bot.commons import log


# TODO : maybe move these to aiohttp web utils file (modeled after commons/web_utils)
def json_response(status: int, data: Any) -> Response:
    """Return a JSON response using aiortc web."""
    return web.Response(
        status=status,
        content_type="application/json",
        text=json.dumps(data),
    )


def respond_ok(data: Any = None) -> Response:
    """Return a JSON response with status ok."""
    return json_response(200, {"status": "ok", "data": data})


def respond_file(path: str, filename: str, content_type: Optional[str] = None) -> Response:
    log.info(f"sending file: {filename} from {path}")
    try:
        content = open(os.path.join(path, filename), "br").read()
    except FileNotFoundError as e:
        log.info(f"Error: File not found. {e}")
        return web.Response(status=404, text="File not found")

    return web.Response(body=content, content_type=content_type)


# see source: https://docs.aiohttp.org/en/stable/logging.html#access-logs
class AccessLogger(AbstractAccessLogger):
    def log(self, request: BaseRequest, response: StreamResponse, time: float) -> None:
        log.info(
            f"Access from {request.remote} "
            f'"{request.method} {request.path} '
            f"done in {time}s: {response.status}"
        )

    @property
    def enabled(self) -> bool:
        """Return True if logger is enabled.

        Override this property if logging is disabled to avoid the
        overhead of calculating details to feed the logger.

        This property may be omitted if logging is always enabled.
        """
        # return self.logger.isEnabledFor(logging.INFO)
        return True
