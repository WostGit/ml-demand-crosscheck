from __future__ import annotations

import time
from unittest.mock import Mock, patch

import pytest
import requests

from retry import (
    DeterministicSourceError,
    RetryExhaustedError,
    TransientSourceError,
    retry_transient,
)
from sources import BaseSourceClient, GoogleTrendsClient, SourceSignal


class _TestClient(BaseSourceClient):
    source_name = "test"
    endpoint = "https://unit.test/source"


def _response(status_code: int = 200, payload: dict | None = None, ok: bool | None = None) -> Mock:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.ok = (200 <= status_code < 300) if ok is None else ok
    response.json.return_value = payload if payload is not None else {
        "score": 0.5,
        "confidence": 0.8,
        "sample_size": 30,
    }
    return response


def test_source_fetch_retries_transient_then_succeeds() -> None:
    client = _TestClient(timeout_seconds=0.01)

    transient = requests.exceptions.ConnectionError("drop")
    with patch("requests.get", side_effect=[transient, _response()]):
        signal = client.fetch("query")

    assert isinstance(signal, SourceSignal)
    assert signal.source == "test"


def test_source_fetch_fails_fast_on_schema_mismatch() -> None:
    client = _TestClient()
    bad_schema = _response(payload={"score": "x", "confidence": 1.0, "sample_size": 1})

    with patch("requests.get", return_value=bad_schema):
        with pytest.raises(DeterministicSourceError):
            client.fetch("query")


def test_source_fetch_raises_after_retry_budget_exhausted() -> None:
    client = _TestClient(timeout_seconds=0.01)

    with patch("requests.get", side_effect=requests.exceptions.Timeout("slow")):
        with pytest.raises(RetryExhaustedError):
            client.fetch("query")


def test_retry_decorator_does_not_retry_deterministic_errors() -> None:
    calls = 0

    @retry_transient(max_attempts=10, base_delay_seconds=0)
    def fn() -> None:
        nonlocal calls
        calls += 1
        raise DeterministicSourceError("bad parse")

    with pytest.raises(DeterministicSourceError):
        fn()

    assert calls == 1


def test_backoff_sequence_for_transient_retries() -> None:
    calls = 0
    sleeps: list[float] = []

    @retry_transient(max_attempts=4, base_delay_seconds=1)
    def fn() -> None:
        nonlocal calls
        calls += 1
        raise TransientSourceError("temporary")

    with patch.object(time, "sleep", side_effect=lambda d: sleeps.append(d)):
        with patch("random.uniform", return_value=0):
            with pytest.raises(RetryExhaustedError):
                fn()

    assert calls == 4
    assert sleeps == [1, 2, 4]


def test_google_client_has_named_source() -> None:
    assert GoogleTrendsClient.source_name == "google_trends"
