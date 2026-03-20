# ML Demand Crosscheck

This repository implements a demand validation engine that separates real demand from noisy signals using four public inputs:

- Google Trends
- eBay sold listings
- Reddit activity
- Amazon autocomplete

## Fault tolerance model

The project uses two resilience layers:

1. **Source-level retries (fine-grained):** each external fetch uses up to 10 attempts with exponential backoff. Retries are only allowed for transient failures (timeouts, connection failures, HTTP 5xx).
2. **Pipeline-level retries (coarse-grained):** GitHub Actions reruns the full pipeline logic up to 10 attempts using exponential backoff.

Deterministic failures (schema mismatch, invalid payload shape, parsing bugs) are designed to fail fast.

## Repository structure

- `demand_engine/retry.py`: retry policy and transient error filter.
- `demand_engine/sources.py`: source adapters wired to retry semantics.
- `demand_engine/pipeline.py`: orchestration entry point.
- `scripts/run_pipeline_with_retries.sh`: workflow-level retry wrapper.
- `.github/workflows/demand-validation.yml`: CI workflow.
