"""Re-emit evaluation metrics + calibration data as JSON for the frontend."""
from __future__ import annotations
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import METRICS_PATH, ensure_dirs, MODEL_INFO_JSON


def main() -> int:
    ensure_dirs()
    if not METRICS_PATH.exists():
        print("[evaluate_model] metrics.json not found; run train_model.py first", file=sys.stderr)
        return 1
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    print("[evaluate_model] Summary:")
    print(f"  n_train             : {metrics['n_train']}")
    print(f"  n_test              : {metrics['n_test']}")
    print(f"  log_loss            : {metrics['log_loss']:.4f}")
    print(f"  brier_score         : {metrics['brier_score']:.4f}")
    print(f"  accuracy            : {metrics['accuracy']:.3f}")
    print(f"  rps                 : {metrics['rps']:.4f}")
    print(f"  baseline_log_loss   : {metrics['baseline_log_loss']:.4f}")
    print(f"  baseline_brier      : {metrics['baseline_brier']:.4f}")
    print(f"  goal_mae_home       : {metrics['goal_mae_home']:.3f}")
    print(f"  goal_mae_away       : {metrics['goal_mae_away']:.3f}")
    print(f"  calibration_bins    : {len(metrics['calibration_bins'])}")
    if metrics.get("classifier_backend"):
        print(f"  classifier_backend  : {metrics['classifier_backend']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
