# ML Demand Crosscheck

This repository contains a demand validation engine that combines noisy public signals from:

- Google Trends
- eBay sold listings
- Reddit
- Amazon autocomplete

## Reliability model

The implementation follows a two-layer fault tolerance strategy:

1. **Source-level transient retries**: all source fetches are retried up to 10 times with exponential backoff (1s, 2s, 4s, ...) when failures are transient (timeouts, connection failures, HTTP 5xx).
2. **Workflow-level retries**: the GitHub Actions job retries the entire validation command up to 10 times with exponential backoff for environment/system instability.

Deterministic issues (invalid schemas, parsing errors, non-retryable HTTP responses) fail fast and do **not** retry.

## CI behavior

The CI workflow runs unit tests (with mocked external HTTP calls) so pull requests are deterministic and do not fail because public endpoints are unavailable.

The CLI (`python main.py`) defaults to dry-run output for the same reason. Set `DEMAND_ENGINE_LIVE=1` to execute live fetches.
