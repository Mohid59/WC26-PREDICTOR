"""Train calibrated classifier + Poisson goal models from feature CSV."""
from __future__ import annotations
import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import (
    ensure_dirs, FEATURES_CSV, MODEL_PATH, METRICS_PATH, MODEL_INFO_JSON
)
from wc_predict.features import FEATURE_COLS
from wc_predict.model import train


def _git_commit() -> str:
    try:
        import subprocess
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        return "no-git"


def main() -> int:
    ensure_dirs()
    df = pd.read_csv(FEATURES_CSV)
    version = f"v0.1-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    art = train(df, FEATURE_COLS, version=version)
    art.save(MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(art.metrics, indent=2), encoding="utf-8")
    info = {
        "version": art.version,
        "trained_at": art.trained_at,
        "feature_cols": art.feature_cols,
        "classifier_backend": getattr(art, "classifier_backend", "logistic"),
        "n_train": art.metrics["n_train"],
        "n_test": art.metrics["n_test"],
        "metrics": {
            k: art.metrics[k] for k in (
                "log_loss", "brier_score", "accuracy", "rps",
                "baseline_log_loss", "baseline_brier",
                "goal_mae_home", "goal_mae_away"
            )
        },
        "git_commit": _git_commit(),
    }
    MODEL_INFO_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_INFO_JSON.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"[train_model] saved {MODEL_PATH}")
    print(
        f"[train_model] classifier={getattr(art, 'classifier_backend', 'logistic')} "
        f"metrics: log_loss={art.metrics['log_loss']:.4f} "
        f"brier={art.metrics['brier_score']:.4f} acc={art.metrics['accuracy']:.3f} "
        f"rps={art.metrics['rps']:.4f}"
    )
    print(f"[train_model] baseline log_loss={art.metrics['baseline_log_loss']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
