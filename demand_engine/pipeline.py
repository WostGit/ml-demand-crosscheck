"""Pipeline orchestration for multi-source demand validation."""

from __future__ import annotations

from .ensemble import DemandSignal, aggregate_signals
from .retry import RetryPolicy
from .sources import (
    amazon_autocomplete_signal,
    ebay_sold_signal,
    google_trends_signal,
    reddit_signal,
)


def run_validation_pipeline(keyword: str, retry_policy: RetryPolicy | None = None) -> DemandSignal:
    """Collect all source signals and aggregate into one demand score."""

    policy = retry_policy or RetryPolicy(max_attempts=10, initial_backoff_seconds=1.0)

    signals = [
        google_trends_signal(keyword, policy),
        ebay_sold_signal(keyword, policy),
        reddit_signal(keyword, policy),
        amazon_autocomplete_signal(keyword, policy),
    ]

    return aggregate_signals(keyword, signals)
