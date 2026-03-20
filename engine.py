"""Demand validation engine that aggregates multiple noisy public signals."""

from __future__ import annotations

from dataclasses import dataclass

from sources import (
    AmazonAutocompleteClient,
    EbaySoldClient,
    GoogleTrendsClient,
    RedditClient,
    SourceSignal,
)


@dataclass(slots=True)
class EnsembleDemandSignal:
    query: str
    weighted_score: float
    participating_sources: int
    total_sample_size: int


class DemandValidationEngine:
    def __init__(self) -> None:
        self.clients = [
            GoogleTrendsClient(),
            EbaySoldClient(),
            RedditClient(),
            AmazonAutocompleteClient(),
        ]

    def validate(self, query: str) -> EnsembleDemandSignal:
        signals = [client.fetch(query) for client in self.clients]
        return self._aggregate(query, signals)

    @staticmethod
    def _aggregate(query: str, signals: list[SourceSignal]) -> EnsembleDemandSignal:
        total_weight = sum(signal.confidence for signal in signals)
        if total_weight <= 0:
            weighted_score = 0.0
        else:
            weighted_score = sum(signal.score * signal.confidence for signal in signals) / total_weight

        total_sample_size = sum(signal.sample_size for signal in signals)

        return EnsembleDemandSignal(
            query=query,
            weighted_score=weighted_score,
            participating_sources=len(signals),
            total_sample_size=total_sample_size,
        )
