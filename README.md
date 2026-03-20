# ml-demand-crosscheck

This repository implements a demand validation engine that cross-checks noisy public signals (Google Trends, eBay sold listings, Reddit, Amazon autocomplete) and aggregates them into an ensemble score.

## Resilience model

The implementation enforces a two-layer retry strategy:

1. **Data source retries (fine-grained)**
   - Up to **10 attempts**.
   - Exponential backoff: `1s, 2s, 4s, 8s, ...`.
   - Retries only for transient failures (timeouts, connection drops, HTTP 5xx).
   - Deterministic errors (schema mismatch, parse errors, invalid payloads) fail immediately.

2. **Pipeline retries (coarse-grained)**
   - GitHub Actions runs the validation step through `nick-fields/retry` with **10 attempts**.
   - This absorbs transient CI instability while still surfacing deterministic failures.

## Design intent

The system is intentionally biased toward recovering from noise and randomness while preserving strict failure semantics for real defects.
