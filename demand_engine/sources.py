"""Source adapters for demand-signal collection."""

from __future__ import annotations

import requests

from demand_engine.retry import retry_transient


class InvalidSourceResponse(ValueError):
    """Raised when a source returns deterministic invalid payloads."""


def _fetch_json(url: str, *, timeout_seconds: int = 20) -> dict:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        raise InvalidSourceResponse(f"Expected object JSON from {url}")
    return data


fetch_google_trends = retry_transient(_fetch_json)
fetch_ebay_sold = retry_transient(_fetch_json)
fetch_reddit_activity = retry_transient(_fetch_json)
fetch_amazon_autocomplete = retry_transient(_fetch_json)
