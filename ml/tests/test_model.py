"""Smoke tests for model training + prediction shape."""
import pandas as pd
import numpy as np
from datetime import date, timedelta
from wc_predict.elo import build_elo_history
from wc_predict.features import build_features, FEATURE_COLS
from wc_predict.model import train, predict_match


def _seed_history(n=300, seed=7):
    import random, math
    rng = random.Random(seed)
    teams = ["A", "B", "C", "D", "E", "F"]
    rows = []
    base = date(2023, 1, 1)
    for i in range(n):
        a, b = rng.sample(teams, 2)
        ra = {"A": 1900, "B": 1750, "C": 1700, "D": 1650, "E": 1600, "F": 1550}[a]
        rb = {"A": 1900, "B": 1750, "C": 1700, "D": 1650, "E": 1600, "F": 1550}[b]
        diff = (ra - rb) / 400
        lh = max(0.2, 1.4 * math.exp(0.3 * diff)); la = max(0.2, 1.4 * math.exp(-0.3 * diff))
        def poi(l):
            L = math.exp(-l); k = 0; p = 1.0
            while True:
                k += 1; p *= rng.random()
                if p <= L: return k - 1
        rows.append((base + timedelta(days=i), a, b, poi(lh), poi(la), "friendly", True))
    df = pd.DataFrame(rows, columns=["date", "home", "away", "home_goals", "away_goals", "tournament", "neutral"])
    return df, teams


def test_training_smoke_and_shape(monkeypatch):
    monkeypatch.setenv("WC26_CLASSIFIER", "hist")
    df, teams = _seed_history()
    teams_meta = pd.DataFrame([{"code": t, "name": t, "confederation": "UEFA",
                                "pot": 1, "is_host": False, "elo_seed": 1500} for t in teams])
    hist = build_elo_history(df)
    feats = build_features(df, hist, teams_meta, include_target=True)
    art = train(feats, FEATURE_COLS, version="test")
    # On 300 synthetic rows we don't assert beating baseline (high variance);
    # just confirm metrics are computed and the model produces well-formed output.
    assert art.metrics["log_loss"] > 0
    assert "calibration_bins" in art.metrics
    assert "goal_mae_home" in art.metrics
    assert art.classifier_backend == "hist"
    sample = {c: float(feats.iloc[-1][c]) for c in FEATURE_COLS}
    out = predict_match(art, sample)
    assert abs(out["p_home"] + out["p_draw"] + out["p_away"] - 1.0) < 1e-3
    assert out["xg_home"] > 0 and out["xg_away"] > 0
    assert len(out["likely_scores"]) == 5
    assert all(0 <= s["prob"] if isinstance(s, dict) else 0 <= s[2] for s in out["likely_scores"])
    # When 1X2 is not a three-way tie, headline is outcome-aligned; when spread is
    # tiny we use the global Poisson mode instead (may disagree with argmax class).
    ph, pdr, pa = out["p_home"], out["p_draw"], out["p_away"]
    spread = max(ph, pdr, pa) - min(ph, pdr, pa)
    h0, a0, _ = out["likely_scores"][0]
    idx = int(np.argmax([ph, pdr, pa]))
    if spread >= 0.15:
        if idx == 0:
            assert h0 > a0
        elif idx == 1:
            assert h0 == a0
        else:
            assert h0 < a0
