"""Retry primitives for transient failures only."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar

import requests

P = ParamSpec("P")
T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 10
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    jitter_ratio: float = 0.2


def is_transient_error(exc: Exception) -> bool:
    """True for retryable network/server failures."""
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return 500 <= exc.response.status_code <= 599
    return False


def retry_transient(
    fn: Callable[P, T],
    *,
    policy: RetryPolicy | None = None,
    transient_predicate: Callable[[Exception], bool] = is_transient_error,
) -> Callable[P, T]:
    """Retry the wrapped function only when failure is transient.

    Deterministic failures are re-raised immediately.
    """

    active_policy = policy or RetryPolicy()

    def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
        attempt = 1
        while True:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # intentionally broad at boundary
                if not transient_predicate(exc):
                    raise
                if attempt >= active_policy.max_attempts:
                    raise

                delay = min(
                    active_policy.base_delay_seconds * (2 ** (attempt - 1)),
                    active_policy.max_delay_seconds,
                )
                jitter = delay * active_policy.jitter_ratio * random.random()
                time.sleep(delay + jitter)
                attempt += 1

    return wrapped
