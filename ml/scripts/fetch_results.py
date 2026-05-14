"""Fetch historical international results.

Tries the public martj42/international_results dataset (CC0) when network is
available. Falls back to a clearly-labelled synthetic seed for offline runs.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import RAW_DIR, ensure_dirs, RESULTS_CSV  # noqa: E402
from wc_predict.sample_data import write_history_csv  # noqa: E402

URL = os.environ.get(
    "WC26_DATA_SOURCE_URL",
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
)


def try_remote() -> bool:
    if os.environ.get("WC26_USE_SAMPLE_DATA", "").lower() == "true":
        return False
    try:
        r = requests.get(URL, timeout=10)
        if r.status_code == 200 and len(r.text) > 5000:
            # Normalise martj42 columns -> our schema
            import io
            import pandas as pd
            df = pd.read_csv(io.StringIO(r.text))
            rename_map = {
                "home_team": "home", "away_team": "away",
                "home_score": "home_goals", "away_score": "away_goals",
            }
            df = df.rename(columns=rename_map)
            if "neutral" not in df.columns:
                df["neutral"] = False
            keep = ["date", "home", "away", "home_goals", "away_goals", "tournament", "neutral"]
            missing = [c for c in keep if c not in df.columns]
            if missing:
                print(f"[fetch_results] remote schema missing {missing}; falling back to sample", file=sys.stderr)
                return False
            df = df[keep].dropna(subset=["home", "away"])
            df["neutral"] = df["neutral"].astype(int)
            # Only keep last 8 years for training relevance and speed
            df["date"] = pd.to_datetime(df["date"]).dt.date
            from datetime import date as _Date
            cutoff = _Date(2018, 1, 1)
            df = df[df["date"] >= cutoff]
            df.to_csv(RESULTS_CSV, index=False)
            print(f"[fetch_results] Fetched & normalised {len(df)} rows (since {cutoff}) -> {RESULTS_CSV}")
            return True
    except Exception as e:
        print(f"[fetch_results] remote fetch failed: {e}", file=sys.stderr)
    return False


def main() -> int:
    ensure_dirs()
    from wc_predict.paths import DATA_STATUS_JSON
    import json, datetime
    DATA_STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    is_real = try_remote()
    if is_real:
        source = "REAL"
        note = "Historical results: martj42/international_results (public CC0 dataset)."
    else:
        source = "SAMPLE"
        note = "Historical results: synthetic seed (Poisson-from-Elo). Update via fetch_results."
        write_history_csv(RESULTS_CSV)
    try:
        current_status = json.loads(DATA_STATUS_JSON.read_text(encoding="utf-8"))
    except Exception:
        current_status = {}
    DATA_STATUS_JSON.write_text(json.dumps({
        "results_source": source,
        "fixtures_source": current_status.get("fixtures_source", "FIFA_OFFICIAL"),
        "is_sample": not is_real,
        "note": note,
        **({"fixtures_note": current_status["fixtures_note"]} if "fixtures_note" in current_status else {}),
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }, indent=2), encoding="utf-8")
    print(f"[fetch_results] Source: {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
