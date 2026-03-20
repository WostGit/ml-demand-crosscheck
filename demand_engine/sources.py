"""Data source adapters for demand validation."""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request

from .retry import (
    DeterministicFailure,
    RetryPolicy,
    TransientFailure,
    TransientHTTPError,
    with_retry,
)


@dataclass(frozen=True)
class SourceSignal:
    source: str
    score: float
    evidence: dict[str, Any]


class InvalidSourceResponse(DeterministicFailure):
    """Raised when source payload is structurally invalid or parse fails."""


def _fetch(url: str, timeout: float = 15.0, headers: dict[str, str] | None = None) -> str:
    req = request.Request(url=url, headers=headers or {})
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            body = response.read().decode("utf-8", errors="replace")
            if status >= 500:
                raise TransientHTTPError(status)
            if status >= 400:
                raise DeterministicFailure(f"HTTP {status} from {url}")
            return body
    except error.HTTPError as exc:
        if exc.code >= 500:
            raise TransientHTTPError(exc.code) from exc
        raise DeterministicFailure(f"HTTP {exc.code} from {url}") from exc
    except (error.URLError, TimeoutError, socket.timeout) as exc:
        raise TransientFailure(str(exc)) from exc


def _fetch_json(url: str, timeout: float = 15.0, headers: dict[str, str] | None = None) -> Any:
    body = _fetch(url, timeout=timeout, headers=headers)
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise InvalidSourceResponse(f"Invalid JSON from {url}") from exc


def google_trends_signal(keyword: str, policy: RetryPolicy | None = None) -> SourceSignal:
    encoded = parse.quote(keyword)
    url = f"https://trends.google.com/trends/api/explore?hl=en-US&q={encoded}"

    def operation() -> SourceSignal:
        payload = _fetch_json(url)
        trend_score = payload.get("default", {}).get("averages", [None])[0]
        if trend_score is None:
            raise InvalidSourceResponse("Google Trends schema mismatch: missing default.averages[0]")
        return SourceSignal("google_trends", float(trend_score), {"url": url})

    return with_retry(operation, policy)


def ebay_sold_signal(keyword: str, policy: RetryPolicy | None = None) -> SourceSignal:
    encoded = parse.quote(keyword)
    url = f"https://www.ebay.com/sch/i.html?_nkw={encoded}&LH_Sold=1"

    def operation() -> SourceSignal:
        html = _fetch(url)
        if "srp-results" not in html:
            raise InvalidSourceResponse("eBay page missing expected srp-results marker")
        sold_count_estimate = html.count("s-item")
        return SourceSignal("ebay_sold", float(sold_count_estimate), {"url": url})

    return with_retry(operation, policy)


def reddit_signal(keyword: str, policy: RetryPolicy | None = None) -> SourceSignal:
    encoded = parse.quote(keyword)
    url = f"https://www.reddit.com/search.json?q={encoded}&sort=top&t=month"
    headers = {"User-Agent": "demand-crosscheck/1.0"}

    def operation() -> SourceSignal:
        payload = _fetch_json(url, headers=headers)
        posts = payload.get("data", {}).get("children")
        if not isinstance(posts, list):
            raise InvalidSourceResponse("Reddit schema mismatch: missing data.children list")
        total_score = sum(float(post.get("data", {}).get("score", 0)) for post in posts[:25])
        return SourceSignal("reddit", total_score, {"url": url, "sample_size": min(len(posts), 25)})

    return with_retry(operation, policy)


def amazon_autocomplete_signal(keyword: str, policy: RetryPolicy | None = None) -> SourceSignal:
    encoded = parse.quote(keyword)
    url = f"https://completion.amazon.com/search/complete?search-alias=aps&mkt=1&q={encoded}"

    def operation() -> SourceSignal:
        payload = _fetch_json(url)
        if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
            raise InvalidSourceResponse("Amazon autocomplete schema mismatch")
        suggestion_count = len(payload[1])
        return SourceSignal("amazon_autocomplete", float(suggestion_count), {"url": url})

    return with_retry(operation, policy)
