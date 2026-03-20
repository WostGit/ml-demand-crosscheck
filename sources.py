"""Data source clients with strict transient/deterministic failure separation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from retry import DeterministicSourceError, TRANSIENT_HTTP_STATUS, TransientSourceError, retry_transient


@dataclass(slots=True)
class SourceSignal:
    source: str
    score: float
    confidence: float
    sample_size: int


class BaseSourceClient:
    source_name: str
    endpoint: str

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    @retry_transient()
    def fetch(self, query: str) -> SourceSignal:
        response = self._request(query)
        payload = self._decode_json(response)
        return self._parse(payload)

    def _request(self, query: str) -> requests.Response:
        try:
            response = requests.get(
                self.endpoint,
                params={"q": query},
                timeout=self.timeout_seconds,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            raise TransientSourceError(f"{self.source_name}: transient network failure") from exc

        if response.status_code in TRANSIENT_HTTP_STATUS:
            raise TransientSourceError(
                f"{self.source_name}: transient HTTP {response.status_code}"
            )

        if not response.ok:
            raise DeterministicSourceError(
                f"{self.source_name}: deterministic HTTP {response.status_code}"
            )

        return response

    def _decode_json(self, response: requests.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise DeterministicSourceError(
                f"{self.source_name}: invalid JSON response schema"
            ) from exc

        if not isinstance(payload, dict):
            raise DeterministicSourceError(
                f"{self.source_name}: response payload must be a JSON object"
            )

        return payload

    def _parse(self, payload: dict[str, Any]) -> SourceSignal:
        required = {"score", "confidence", "sample_size"}
        missing = required.difference(payload)
        if missing:
            raise DeterministicSourceError(
                f"{self.source_name}: missing required keys {sorted(missing)}"
            )

        try:
            score = float(payload["score"])
            confidence = float(payload["confidence"])
            sample_size = int(payload["sample_size"])
        except (TypeError, ValueError) as exc:
            raise DeterministicSourceError(
                f"{self.source_name}: schema mismatch in signal fields"
            ) from exc

        return SourceSignal(
            source=self.source_name,
            score=score,
            confidence=confidence,
            sample_size=sample_size,
        )


class GoogleTrendsClient(BaseSourceClient):
    source_name = "google_trends"
    endpoint = "https://example.invalid/google-trends"


class EbaySoldClient(BaseSourceClient):
    source_name = "ebay_sold"
    endpoint = "https://example.invalid/ebay-sold"


class RedditClient(BaseSourceClient):
    source_name = "reddit"
    endpoint = "https://example.invalid/reddit"


class AmazonAutocompleteClient(BaseSourceClient):
    source_name = "amazon_autocomplete"
    endpoint = "https://example.invalid/amazon-autocomplete"
