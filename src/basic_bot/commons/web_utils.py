"""
Utility functions for handling Flask web responses and requests.
"""

import json


def json_response(app, data):
    """Return a JSON response."""
    response = app.response_class(
        response=json.dumps(data), status=200, mimetype="application/json"
    )
    return response


def respond_ok(app, data=None):
    """Return a JSON response with status ok."""
    return json_response(app, {"status": "ok", "data": data})


def respond_not_ok(app, status, data):
    """Return a JSON response with status not ok."""
    return json_response(app, {"status": status, "data": data})
