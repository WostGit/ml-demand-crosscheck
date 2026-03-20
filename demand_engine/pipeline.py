"""Ensemble orchestrator for market-demand validation."""

from __future__ import annotations

from dataclasses import dataclass

from demand_engine.sources import (
    fetch_amazon_autocomplete,
    fetch_ebay_sold,
    fetch_google_trends,
    fetch_reddit_activity,
)


@dataclass(frozen=True)
class DemandSignal:
    google_trends: dict
    ebay_sold: dict
    reddit: dict
    amazon_autocomplete: dict


def collect_signals(base_urls: dict[str, str]) -> DemandSignal:
    """Collect all source inputs with source-level transient retry semantics."""
    return DemandSignal(
        google_trends=fetch_google_trends(base_urls["google_trends"]),
        ebay_sold=fetch_ebay_sold(base_urls["ebay_sold"]),
        reddit=fetch_reddit_activity(base_urls["reddit"]),
        amazon_autocomplete=fetch_amazon_autocomplete(base_urls["amazon_autocomplete"]),
    )
