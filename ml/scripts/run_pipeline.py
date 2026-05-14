"""End-to-end pipeline: fetch -> features -> train -> evaluate -> predict -> simulate."""
from __future__ import annotations
import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import ensure_dirs, DATA_STATUS_JSON


def main() -> int:
    ensure_dirs()
    import subprocess
    here = Path(__file__).parent
    steps = [
        ["fetch_results.py"],
        ["fetch_fixtures.py"],
        ["build_features.py"],
        ["train_model.py"],
        ["evaluate_model.py"],
        ["predict_fixtures.py"],
        ["simulate_tournament.py"],
    ]
    for step in steps:
        print(f"\n=== {step[0]} ===")
        rc = subprocess.call([sys.executable, str(here / step[0])])
        if rc != 0:
            print(f"[run_pipeline] step {step[0]} failed with rc={rc}", file=sys.stderr)
            return rc

    # data_status.json already written by fetch_results.py — leave it intact
    print("\n[run_pipeline] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
