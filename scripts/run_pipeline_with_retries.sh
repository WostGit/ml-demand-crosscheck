#!/usr/bin/env bash
set -euo pipefail

max_attempts="${MAX_ATTEMPTS:-10}"
attempt=1

while [ "$attempt" -le "$max_attempts" ]; do
  echo "[pipeline] attempt ${attempt}/${max_attempts}"
  if python -m demand_engine.pipeline; then
    echo "[pipeline] success"
    exit 0
  fi

  if [ "$attempt" -eq "$max_attempts" ]; then
    echo "[pipeline] failed after ${max_attempts} attempts"
    exit 1
  fi

  sleep_seconds=$((2 ** (attempt - 1)))
  if [ "$sleep_seconds" -gt 60 ]; then
    sleep_seconds=60
  fi
  echo "[pipeline] retrying in ${sleep_seconds}s"
  sleep "$sleep_seconds"
  attempt=$((attempt + 1))
done
