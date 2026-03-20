from demand_validation.retry import DeterministicError, RetryPolicy, TransientError, retry_transient


def test_retry_transient_retries_until_success():
    calls = {"count": 0}
    sleeps = []

    def op():
        calls["count"] += 1
        if calls["count"] < 4:
            raise TransientError("temporary")
        return "ok"

    result = retry_transient(
        op,
        policy=RetryPolicy(max_attempts=10, base_delay_seconds=1),
        sleep=sleeps.append,
    )

    assert result == "ok"
    assert calls["count"] == 4
    assert sleeps == [1, 2, 4]


def test_retry_transient_fails_fast_on_deterministic_error():
    calls = {"count": 0}

    def op():
        calls["count"] += 1
        raise DeterministicError("bad schema")

    try:
        retry_transient(op, policy=RetryPolicy(max_attempts=10))
        assert False, "expected DeterministicError"
    except DeterministicError:
        pass

    assert calls["count"] == 1
