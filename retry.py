"""Retry utilities for transient external I/O failures."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import requests

F = TypeVar("F", bound=Callable[..., object])

TRANSIENT_HTTP_STATUS = {500, 502, 503, 504}
MAX_ATTEMPTS = 10


class RetryExhaustedError(RuntimeError):
    """Raised when all retry attempts are exhausted for a transient operation."""


class DeterministicSourceError(RuntimeError):
    """Raised when a source fails deterministically and should not be retried."""


class TransientSourceError(RuntimeError):
    """Raised when a source encounters a transient failure that is retryable."""


def is_transient_exception(exc: BaseException) -> bool:
    """Return True when an exception represents a transient failure."""
    if isinstance(exc, TransientSourceError):
        return True

    if isinstance(exc, requests.exceptions.Timeout):
        return True

    if isinstance(exc, requests.exceptions.ConnectionError):
        return True

    if isinstance(exc, requests.exceptions.HTTPError):
        response = getattr(exc, "response", None)
        return bool(response and response.status_code in TRANSIENT_HTTP_STATUS)

    return False


def retry_transient(max_attempts: int = MAX_ATTEMPTS, base_delay_seconds: float = 1.0) -> Callable[[F], F]:
    """Retry wrapped function using exponential backoff for transient failures only."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            attempt = 1
            last_exc: BaseException | None = None

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    if not is_transient_exception(exc):
                        raise

                    last_exc = exc
                    if attempt == max_attempts:
                        break

                    jitter = random.uniform(0, 0.25)
                    delay = (base_delay_seconds * (2 ** (attempt - 1))) + jitter
                    time.sleep(delay)
                    attempt += 1

            raise RetryExhaustedError(
                f"Operation failed after {max_attempts} transient attempts"
            ) from last_exc

        return wrapper  # type: ignore[return-value]

    return decorator
