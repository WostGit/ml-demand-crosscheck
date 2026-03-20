"""CLI entrypoint for demand validation engine.

By default, this command runs in dry-run mode so CI does not depend on live
third-party endpoints. Set `DEMAND_ENGINE_LIVE=1` to execute real fetches.
"""

from __future__ import annotations

import json
import os

from engine import DemandValidationEngine, EnsembleDemandSignal


DRY_RUN_SIGNAL = EnsembleDemandSignal(
    query="wireless gaming mouse",
    weighted_score=0.62,
    participating_sources=4,
    total_sample_size=1280,
)


if __name__ == "__main__":
    live_mode = os.getenv("DEMAND_ENGINE_LIVE", "0") == "1"
    if live_mode:
        signal = DemandValidationEngine().validate("wireless gaming mouse")
    else:
        signal = DRY_RUN_SIGNAL

    print(json.dumps(signal.__dict__, sort_keys=True))
