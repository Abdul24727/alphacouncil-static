"""Small JSON-over-HTTPS client for the two outside services the API calls (Google sign-in,
Moyasar), on the standard library: no new dependency, a timeout on every call, and errors
returned as data rather than raised."""

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TIMEOUT_S = 20


class Reply:
    def __init__(self, status: int, body: Any):
        self.status, self.body = status, body

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


def basic(user: str, password: str = "") -> dict[str, str]:
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


def call(method: str, url: str, *, json_body: Any = None, form: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> Reply:
    data, hdrs = None, {"Accept": "application/json", **(headers or {})}
    if json_body is not None:
        data, hdrs["Content-Type"] = json.dumps(json_body).encode(), "application/json"
    elif form is not None:
        data, hdrs["Content-Type"] = urllib.parse.urlencode(form).encode(), "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:  # noqa: S310 (https URLs from settings)
            raw = r.read()
            return Reply(r.status, json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return Reply(e.code, json.loads(raw) if raw else None)
        except ValueError:
            return Reply(e.code, None)
    except (urllib.error.URLError, TimeoutError, OSError):
        return Reply(0, None)
