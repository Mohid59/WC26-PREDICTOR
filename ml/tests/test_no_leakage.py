"""Critical: verify feature engineering does not leak future information."""
import pandas as pd
from datetime import date
from wc_predict.elo import build_elo_history
from wc_predict.features import build_features


def _df(rows):
    return pd.DataFrame(rows, columns=["date", "home", "away", "home_goals", "away_goals", "tournament", "neutral"])


def test_first_match_uses_default_form():
    """Before any history, form features should be at their default (0 or 0.5)."""
    df = _df([
        (date(2024, 1, 1), "A", "B", 2, 1, "friendly", True),
        (date(2024, 2, 1), "A", "B", 0, 3, "friendly", True),
    ])
    teams = pd.DataFrame([
        {"code": "A", "name": "A", "confederation": "UEFA", "pot": 1, "is_host": False, "elo_seed": 1500},
        {"code": "B", "name": "B", "confederation": "UEFA", "pot": 1, "is_host": False, "elo_seed": 1500},
    ])
    hist = build_elo_history(df)
    feats = build_features(df, hist, teams, include_target=True)
    first = feats.iloc[0]
    assert first["form5_diff"] == 0.0  # both 0.5 default -> diff 0
    assert first["form10_diff"] == 0.0


def test_second_match_reflects_first():
    """After A beats B once, A's form-5 should be higher than B's."""
    df = _df([
        (date(2024, 1, 1), "A", "B", 2, 0, "friendly", True),
        (date(2024, 2, 1), "A", "B", 0, 0, "friendly", True),
    ])
    teams = pd.DataFrame([
        {"code": "A", "name": "A", "confederation": "UEFA", "pot": 1, "is_host": False, "elo_seed": 1500},
        {"code": "B", "name": "B", "confederation": "UEFA", "pot": 1, "is_host": False, "elo_seed": 1500},
    ])
    hist = build_elo_history(df)
    feats = build_features(df, hist, teams, include_target=True)
    second = feats.iloc[1]
    assert second["form5_diff"] > 0
    assert second["elo_home"] > second["elo_away"]


def test_elo_before_match_is_pre_match():
    """ELO value at match M must equal ELO computed using only matches strictly before M."""
    df = _df([
        (date(2024, 1, 1), "A", "B", 2, 0, "friendly", True),
        (date(2024, 6, 1), "A", "B", 1, 1, "friendly", True),
        (date(2024, 8, 1), "A", "B", 0, 2, "friendly", True),
    ])
    teams = pd.DataFrame([
        {"code": "A", "name": "A", "confederation": "UEFA", "pot": 1, "is_host": False, "elo_seed": 1500},
        {"code": "B", "name": "B", "confederation": "UEFA", "pot": 1, "is_host": False, "elo_seed": 1500},
    ])
    hist = build_elo_history(df)
    feats = build_features(df, hist, teams, include_target=True)
    # The feature elo for match 3 must NOT use match-3 result
    e3_home = feats.iloc[2]["elo_home"]
    # Re-derive using only first two matches
    short = df.iloc[:2].reset_index(drop=True)
    hist_short = build_elo_history(short)
    expected = hist_short.final_ratings["A"]
    assert abs(e3_home - expected) < 1e-6
