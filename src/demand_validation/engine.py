"""Demand validation engine that aggregates multiple noisy predictors."""

from __future__ import annotations

from dataclasses import dataclass

from .retry import RetryPolicy
from .sources import SourceSignal, fetch_source_signal


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str


@dataclass(frozen=True)
class EnsembleResult:
    aggregate_score: float
    by_source: dict[str, float]


class DemandValidationEngine:
    """Cross-check demand signals from multiple imperfect public sources."""

    def __init__(self, sources: list[SourceConfig], *, retry_policy: RetryPolicy | None = None):
        self._sources = sources
        self._retry_policy = retry_policy or RetryPolicy(max_attempts=10, base_delay_seconds=1.0)

    def collect(self) -> list[SourceSignal]:
        return [
            fetch_source_signal(cfg.name, cfg.url, policy=self._retry_policy)
            for cfg in self._sources
        ]

    def validate(self) -> EnsembleResult:
        signals = self.collect()
        if not signals:
            return EnsembleResult(aggregate_score=0.0, by_source={})

        by_source = {signal.name: signal.score for signal in signals}
        aggregate = sum(by_source.values()) / len(by_source)
        return EnsembleResult(aggregate_score=aggregate, by_source=by_source)
