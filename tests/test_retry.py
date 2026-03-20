from __future__ import annotations

import pytest

from demand_engine.retry import (
    DeterministicFailure,
    RetryPolicy,
    TransientFailure,
    compute_backoffs,
    with_retry,
)


def test_compute_backoffs_is_exponential() -> None:
    policy = RetryPolicy(max_attempts=10, initial_backoff_seconds=1)
    assert list(compute_backoffs(policy)) == [1, 2, 4, 8, 16, 32, 64, 128, 256]


def test_retries_transient_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"count": 0}

    def op() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TransientFailure("temporary")
        return "ok"

    sleeps: list[float] = []
    monkeypatch.setattr("demand_engine.retry.time.sleep", lambda n: sleeps.append(n))

    result = with_retry(op, RetryPolicy(max_attempts=10, initial_backoff_seconds=1))

    assert result == "ok"
    assert attempts["count"] == 3
    assert sleeps == [1, 2]


def test_fails_fast_for_deterministic_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("demand_engine.retry.time.sleep", lambda _n: None)

    with pytest.raises(DeterministicFailure):
        with_retry(lambda: (_ for _ in ()).throw(DeterministicFailure("bad schema")))
