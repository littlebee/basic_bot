"""
Utility functions for handling Flask web responses and requests.
"""

import json
from typing import Any, Optional
from flask import Response, Flask


def json_response(app: Flask, data: Any) -> Response:
    """Return a JSON response."""
    response = app.response_class(
        response=json.dumps(data), status=200, mimetype="application/json"
    )
    return response


def respond_ok(app: Flask, data: Optional[Any] = None) -> Response:
    """Return a JSON response with status ok."""
    return json_response(app, {"status": "ok", "data": data})


def respond_not_ok(app: Flask, status: str, data: Any) -> Response:
    """Return a JSON response with status not ok."""
    return json_response(app, {"status": status, "data": data})
