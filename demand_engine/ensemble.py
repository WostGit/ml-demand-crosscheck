"""Ensemble-style aggregation across imperfect demand predictors."""

from __future__ import annotations

from dataclasses import dataclass

from .sources import SourceSignal


@dataclass(frozen=True)
class DemandSignal:
    keyword: str
    normalized_score: float
    sources: list[SourceSignal]


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    vmax = max(values)
    if vmax <= 0:
        return [0.0 for _ in values]
    return [value / vmax for value in values]


def aggregate_signals(keyword: str, signals: list[SourceSignal]) -> DemandSignal:
    """Aggregate source signals into a resilient ensemble score."""

    normalized = _normalize([signal.score for signal in signals])
    ensemble_score = sum(normalized) / len(normalized) if normalized else 0.0
    return DemandSignal(keyword=keyword, normalized_score=ensemble_score, sources=signals)
