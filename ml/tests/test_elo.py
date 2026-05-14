import pandas as pd
from datetime import date
from wc_predict.elo import build_elo_history, expected_score


def test_expected_score_symmetry():
    p = expected_score(1500, 1500)
    assert abs(p - 0.5) < 1e-9


def test_expected_score_stronger_wins_more():
    assert expected_score(2000, 1500) > expected_score(1500, 2000)


def _df(rows):
    return pd.DataFrame(rows, columns=["date", "home", "away", "home_goals", "away_goals", "tournament", "neutral"])


def test_elo_updates_monotone_for_consistent_winner():
    df = _df([
        (date(2024, 1, 1), "A", "B", 3, 0, "friendly", True),
        (date(2024, 2, 1), "A", "B", 2, 0, "friendly", True),
        (date(2024, 3, 1), "A", "B", 1, 0, "friendly", True),
    ])
    hist = build_elo_history(df)
    ratings_a = [r for _, r in hist.history["A"]]
    ratings_b = [r for _, r in hist.history["B"]]
    assert ratings_a == sorted(ratings_a)
    assert ratings_b == sorted(ratings_b, reverse=True)


def test_elo_rating_lookup_is_pre_match():
    df = _df([
        (date(2024, 1, 1), "A", "B", 3, 0, "friendly", True),
        (date(2024, 2, 1), "A", "B", 2, 0, "friendly", True),
    ])
    hist = build_elo_history(df)
    # On 2024-01-15 only the first match has occurred
    r_after_first = hist.rating_on_or_before("A", "2024-01-15")
    r_after_second = hist.rating_on_or_before("A", "2024-02-15")
    assert r_after_second > r_after_first
