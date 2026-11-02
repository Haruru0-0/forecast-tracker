"""Data sources and their shared HTTP helper."""

from __future__ import annotations

import time

import requests

from ftracker.series import SourceError

ATTEMPTS = 3
BACKOFF_SECONDS = 1.0
TIMEOUT_SECONDS = 30

_sleep = time.sleep  # replaced in tests


def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             attempts: int = ATTEMPTS, timeout: float = TIMEOUT_SECONDS) -> dict:
    """GET url and return parsed JSON; retry with backoff, then raise SourceError."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt < attempts - 1:
                _sleep(BACKOFF_SECONDS * 2**attempt)
    raise SourceError(f"GET {url} failed after {attempts} attempts: {last}") from last
