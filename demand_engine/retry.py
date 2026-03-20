"""Retry primitives with strict transient/deterministic failure separation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Defines retry behavior for transient failures."""

    max_attempts: int = 10
    initial_backoff_seconds: float = 1.0


class DeterministicFailure(Exception):
    """A failure type that must fail fast and never be retried."""


class TransientFailure(Exception):
    """A failure type representing temporary failures safe to retry."""


class TransientHTTPError(TransientFailure):
    """A transient HTTP error with status code metadata."""

    def __init__(self, status_code: int, message: str = "") -> None:
        super().__init__(message or f"HTTP {status_code}")
        self.status_code = status_code


TRANSIENT_HTTP_STATUS_CODES: set[int] = {500, 502, 503, 504}


def is_transient_exception(exc: Exception) -> bool:
    """Return True when exception likely represents temporary instability."""

    if isinstance(exc, TransientFailure):
        return True

    if isinstance(exc, TimeoutError):
        return True

    return False


def compute_backoffs(policy: RetryPolicy) -> Iterable[float]:
    """Yield exponential backoff durations for each retry pause."""

    delay = policy.initial_backoff_seconds
    for _ in range(policy.max_attempts - 1):
        yield delay
        delay *= 2


def with_retry(operation: Callable[[], T], policy: RetryPolicy | None = None) -> T:
    """Run an operation with retry semantics for transient failures only."""

    policy = policy or RetryPolicy()
    backoffs = list(compute_backoffs(policy))

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return operation()
        except DeterministicFailure:
            raise
        except Exception as exc:
            if attempt >= policy.max_attempts or not is_transient_exception(exc):
                raise
            time.sleep(backoffs[attempt - 1])

    raise RuntimeError("unreachable")
