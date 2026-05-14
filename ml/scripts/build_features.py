"""Build feature CSVs from raw data."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wc_predict.paths import (
    ensure_dirs, RESULTS_CSV, TEAMS_CSV, FIXTURES_CSV, FEATURES_CSV, PROCESSED_DIR
)
from wc_predict.data import load_results, load_teams, load_fixtures
from wc_predict.elo import build_elo_history
from wc_predict.features import build_features, build_fixture_features, FEATURE_COLS


def main() -> int:
    ensure_dirs()
    results = load_results(RESULTS_CSV)
    teams = load_teams(TEAMS_CSV)
    seed_ratings = dict(zip(teams["code"], teams["elo_seed"]))
    elo = build_elo_history(results, seed_ratings=seed_ratings)
    feats = build_features(results, elo, teams, include_target=True)
    feats.to_csv(FEATURES_CSV, index=False)
    print(f"[build_features] Wrote {len(feats)} rows to {FEATURES_CSV}")
    # Fixture features
    fx = load_fixtures(FIXTURES_CSV)
    fx_feats = build_fixture_features(fx, feats, elo, teams)
    fx_path = PROCESSED_DIR / "fixture_features.csv"
    fx_feats.to_csv(fx_path, index=False)
    print(f"[build_features] Wrote {len(fx_feats)} fixture rows to {fx_path}")
    print(f"[build_features] feature_cols: {FEATURE_COLS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
