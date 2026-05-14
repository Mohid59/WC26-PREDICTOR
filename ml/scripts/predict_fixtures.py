"""Generate per-fixture predictions JSON consumed by the Next.js frontend."""
from __future__ import annotations
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import (
    ensure_dirs, FIXTURES_CSV, TEAMS_CSV, MODEL_PATH, PROCESSED_DIR,
    PREDICTIONS_JSON, FIXTURES_JSON, TEAMS_JSON
)
from wc_predict.model import ModelArtifacts, predict_match
from wc_predict.data import load_teams, load_fixtures
from wc_predict.features import FEATURE_COLS


def main() -> int:
    ensure_dirs()
    art = ModelArtifacts.load(MODEL_PATH)
    fx = load_fixtures(FIXTURES_CSV)
    teams = load_teams(TEAMS_CSV)
    fx_feats = pd.read_csv(PROCESSED_DIR / "fixture_features.csv")

    fx_feats_idx = fx_feats.set_index("match_id")
    known_teams = set(teams["code"])
    preds = []
    now = datetime.utcnow().isoformat() + "Z"
    for fxr in fx.itertuples(index=False):
        if fxr.stage != "group" or fxr.home not in known_teams or fxr.away not in known_teams:
            continue
        if fxr.match_id not in fx_feats_idx.index:
            continue
        row = fx_feats_idx.loc[fxr.match_id]
        feat = {c: float(row[c]) for c in FEATURE_COLS}
        out = predict_match(art, feat)
        # round for JSON cleanliness
        rec = {
            "match_id": fxr.match_id,
            "date": str(fxr.date),
            "kickoff": getattr(fxr, "kickoff", None),
            "stage": getattr(fxr, "stage", "group"),
            "group": getattr(fxr, "group", None),
            "venue": getattr(fxr, "venue", None),
            "home": fxr.home,
            "away": fxr.away,
            "p_home": round(out["p_home"], 4),
            "p_draw": round(out["p_draw"], 4),
            "p_away": round(out["p_away"], 4),
            "xg_home": round(out["xg_home"], 3),
            "xg_away": round(out["xg_away"], 3),
            "likely_scores": [
                {"home_goals": int(h), "away_goals": int(a), "prob": round(float(p), 4)}
                for (h, a, p) in out["likely_scores"]
            ],
            "confidence": round(out["confidence"], 4),
            "top_features": [
                {"name": n, "contribution": round(v, 4)} for (n, v) in out["top_features"]
            ],
            "model_version": art.version,
            "generated_at": now,
        }
        preds.append(rec)

    PREDICTIONS_JSON.write_text(json.dumps({"items": preds, "generated_at": now, "model_version": art.version}, indent=2), encoding="utf-8")
    FIXTURES_JSON.write_text(json.dumps(
        {"items": json.loads(fx.assign(date=fx["date"].astype(str)).to_json(orient="records"))},
        indent=2,
    ), encoding="utf-8")
    TEAMS_JSON.write_text(json.dumps(
        {"items": json.loads(teams.to_json(orient="records"))}, indent=2
    ), encoding="utf-8")
    print(f"[predict_fixtures] wrote {len(preds)} predictions -> {PREDICTIONS_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
