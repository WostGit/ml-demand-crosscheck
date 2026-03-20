"""Retry utilities with strict transient/deterministic failure semantics."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


class TransientError(RuntimeError):
    """Raised when an operation fails for a transient reason."""


class DeterministicError(RuntimeError):
    """Raised when an operation fails for a deterministic reason."""


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for exponential backoff retries."""

    max_attempts: int = 10
    base_delay_seconds: float = 1.0


def retry_transient(
    operation: Callable[[], T],
    *,
    policy: RetryPolicy = RetryPolicy(),
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """
    Run `operation` with exponential backoff for transient failures only.

    - Retries up to `max_attempts` on `TransientError`.
    - Fails fast on `DeterministicError`.
    - Any unknown exception is treated as deterministic to avoid masking bugs.
    """

    attempt = 1
    delay = policy.base_delay_seconds

    while True:
        try:
            return operation()
        except DeterministicError:
            raise
        except TransientError:
            if attempt >= policy.max_attempts:
                raise
            sleep(delay)
            delay *= 2
            attempt += 1
        except Exception as exc:  # noqa: BLE001
            raise DeterministicError(
                f"Unexpected deterministic failure from {operation.__name__}"
            ) from exc
