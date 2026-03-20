"""Source adapters for public demand signals."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .retry import DeterministicError, RetryPolicy, TransientError, retry_transient


@dataclass(frozen=True)
class SourceSignal:
    name: str
    score: float
    metadata: dict[str, Any]


def _http_get_json(url: str, timeout: float = 8.0) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "ml-demand-crosscheck/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - trusted caller
            code = response.status
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        if 500 <= exc.code <= 599:
            raise TransientError(f"Server error {exc.code} for {url}") from exc
        raise DeterministicError(f"Non-retryable HTTP error {exc.code} for {url}") from exc
    except URLError as exc:
        raise TransientError(f"Connection failure for {url}") from exc
    except TimeoutError as exc:
        raise TransientError(f"Timeout for {url}") from exc

    if 500 <= code <= 599:
        raise TransientError(f"Server error {code} for {url}")
    if code >= 400:
        raise DeterministicError(f"Non-retryable HTTP status {code} for {url}")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DeterministicError(f"Invalid JSON response from {url}") from exc

    if not isinstance(payload, dict):
        raise DeterministicError(f"Expected object JSON schema from {url}")

    return payload


def fetch_source_signal(name: str, url: str, *, policy: RetryPolicy = RetryPolicy()) -> SourceSignal:
    """Fetch a source signal with strict transient retry semantics."""

    def op() -> SourceSignal:
        payload = _http_get_json(url)
        try:
            score = float(payload["score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DeterministicError(f"Schema mismatch for {name}: expected numeric 'score'") from exc
        return SourceSignal(name=name, score=score, metadata=payload)

    return retry_transient(op, policy=policy)
