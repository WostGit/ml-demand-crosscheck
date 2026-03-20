# ML Demand Crosscheck

This repository validates market demand by cross-checking independent free public data sources:

- Google Trends
- eBay sold listings
- Reddit
- Amazon autocomplete

## Resilience model

The system applies two layers of fault tolerance:

1. **Source-level retries**: every network fetch uses up to 10 attempts with exponential backoff (`1s, 2s, 4s, ...`) and retries only transient failures (timeouts, connection errors, HTTP 5xx).
2. **Workflow-level retries**: GitHub Actions retries the whole validation run up to 10 times to handle CI/environment instability.

Deterministic failures (schema mismatches, invalid response formats, parsing defects) fail fast.

## Run locally

```bash
pip install -e .[dev]
pytest -q
```
