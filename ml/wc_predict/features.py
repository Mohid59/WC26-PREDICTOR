"""Feature engineering with strict no-leakage guarantee.

Every feature for match M is computed using only events strictly before M's date.
The leakage tests in ``ml/tests/test_no_leakage.py`` verify this property.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import timedelta, date as Date
from collections import defaultdict, deque
from .elo import EloHistory, expected_score, HOME_ADV_ELO


FEATURE_COLS = [
    "elo_diff",
    "elo_home",
    "elo_away",
    "form5_diff",
    "form10_diff",
    "gf5_home", "gf5_away",
    "ga5_home", "ga5_away",
    "attack_home", "attack_away",
    "defense_home", "defense_away",
    "rest_diff",
    "host_home", "host_away",
    "same_confederation",
    "neutral",
]


def _form_points(results: int) -> float:
    return results  # placeholder; kept for clarity


def build_features(
    results: pd.DataFrame,
    elo_hist: EloHistory,
    teams_meta: pd.DataFrame,
    include_target: bool = True,
) -> pd.DataFrame:
    """Build a feature row per historical match (or per fixture if include_target=False).

    Features use ratings AS OF (date_of_match - 1 day) so that leakage is impossible.
    """
    meta = teams_meta.set_index("code")
    rows: list[dict] = []
    # Per-team rolling structures keyed by code
    last_dates: dict[str, Date] = {}
    recent_results: dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
    recent_goals_for: dict[str, deque] = defaultdict(lambda: deque(maxlen=5))
    recent_goals_against: dict[str, deque] = defaultdict(lambda: deque(maxlen=5))
    season_attack: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
    season_defense: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

    # Process chronologically; for each match, snapshot current pre-match stats
    for row in results.itertuples(index=False):
        home, away = row.home, row.away
        date_iso = str(row.date)
        day_before = (pd.to_datetime(date_iso) - pd.Timedelta(days=1)).date().isoformat()
        elo_home = elo_hist.rating_on_or_before(home, day_before, default=1500.0)
        elo_away = elo_hist.rating_on_or_before(away, day_before, default=1500.0)

        def _avg(d: deque, default: float = 0.0) -> float:
            return float(sum(d) / len(d)) if d else default

        feat = {
            "match_id": getattr(row, "match_id", f"H-{len(rows):06d}"),
            "date": date_iso,
            "home": home,
            "away": away,
            "elo_home": elo_home,
            "elo_away": elo_away,
            "elo_diff": elo_home - elo_away,
            "form5_diff": _avg(deque(list(recent_results[home])[-5:]), 0.5) - _avg(deque(list(recent_results[away])[-5:]), 0.5),
            "form10_diff": _avg(recent_results[home], 0.5) - _avg(recent_results[away], 0.5),
            "gf5_home": _avg(recent_goals_for[home], 1.2),
            "gf5_away": _avg(recent_goals_for[away], 1.2),
            "ga5_home": _avg(recent_goals_against[home], 1.2),
            "ga5_away": _avg(recent_goals_against[away], 1.2),
            "attack_home": _avg(season_attack[home], 1.3),
            "attack_away": _avg(season_attack[away], 1.3),
            "defense_home": _avg(season_defense[home], 1.3),
            "defense_away": _avg(season_defense[away], 1.3),
            "rest_diff": (
                ((pd.to_datetime(date_iso).date() - last_dates[home]).days if home in last_dates else 14)
                - ((pd.to_datetime(date_iso).date() - last_dates[away]).days if away in last_dates else 14)
            ),
            "host_home": int(bool(meta.loc[home, "is_host"])) if home in meta.index else 0,
            "host_away": int(bool(meta.loc[away, "is_host"])) if away in meta.index else 0,
            "same_confederation": int(
                home in meta.index and away in meta.index and
                meta.loc[home, "confederation"] == meta.loc[away, "confederation"]
            ),
            "neutral": int(bool(row.neutral)),
        }
        if include_target:
            gd = int(row.home_goals) - int(row.away_goals)
            feat["target"] = 0 if gd > 0 else (1 if gd == 0 else 2)  # home/draw/away
            feat["home_goals"] = int(row.home_goals)
            feat["away_goals"] = int(row.away_goals)
        rows.append(feat)

        # NOW update post-match rolling stats so future matches see them
        last_dates[home] = pd.to_datetime(date_iso).date()
        last_dates[away] = pd.to_datetime(date_iso).date()
        gh, ga = int(row.home_goals), int(row.away_goals)
        recent_results[home].append(1.0 if gh > ga else (0.5 if gh == ga else 0.0))
        recent_results[away].append(1.0 if ga > gh else (0.5 if gh == ga else 0.0))
        recent_goals_for[home].append(gh); recent_goals_for[away].append(ga)
        recent_goals_against[home].append(ga); recent_goals_against[away].append(gh)
        season_attack[home].append(gh); season_attack[away].append(ga)
        season_defense[home].append(ga); season_defense[away].append(gh)
    df = pd.DataFrame(rows)
    return df


def build_fixture_features(
    fixtures: pd.DataFrame,
    history_features: pd.DataFrame,
    elo_hist: EloHistory,
    teams_meta: pd.DataFrame,
) -> pd.DataFrame:
    """Produce features for upcoming fixtures using stats up to each fixture's date."""
    meta = teams_meta.set_index("code")
    # Build per-team rolling tail using last entries from history_features
    history_features = history_features.sort_values("date").reset_index(drop=True)
    rows: list[dict] = []
    # Per team latest snapshot from history (post-update)
    latest_form: dict[str, list[float]] = defaultdict(list)
    latest_gf: dict[str, list[float]] = defaultdict(list)
    latest_ga: dict[str, list[float]] = defaultdict(list)
    latest_attack: dict[str, list[float]] = defaultdict(list)
    latest_defense: dict[str, list[float]] = defaultdict(list)
    last_dates: dict[str, Date] = {}
    for r in history_features.itertuples(index=False):
        # Re-derive results from goals to keep deque correct
        gh, ga = int(getattr(r, "home_goals", 0)), int(getattr(r, "away_goals", 0))
        latest_form[r.home].append(1.0 if gh > ga else (0.5 if gh == ga else 0.0))
        latest_form[r.away].append(1.0 if ga > gh else (0.5 if gh == ga else 0.0))
        latest_gf[r.home].append(gh); latest_gf[r.away].append(ga)
        latest_ga[r.home].append(ga); latest_ga[r.away].append(gh)
        latest_attack[r.home].append(gh); latest_attack[r.away].append(ga)
        latest_defense[r.home].append(ga); latest_defense[r.away].append(gh)
        last_dates[r.home] = pd.to_datetime(r.date).date()
        last_dates[r.away] = pd.to_datetime(r.date).date()

    def avg(seq: list[float], n: int, default: float) -> float:
        if not seq:
            return default
        tail = seq[-n:]
        return float(sum(tail) / len(tail))

    for fx in fixtures.itertuples(index=False):
        home, away = fx.home, fx.away
        date_iso = str(fx.date)
        day_before = (pd.to_datetime(date_iso) - pd.Timedelta(days=1)).date().isoformat()
        elo_home = elo_hist.rating_on_or_before(home, day_before, default=1500.0)
        elo_away = elo_hist.rating_on_or_before(away, day_before, default=1500.0)
        feat = {
            "match_id": fx.match_id,
            "date": date_iso,
            "home": home,
            "away": away,
            "elo_home": elo_home,
            "elo_away": elo_away,
            "elo_diff": elo_home - elo_away,
            "form5_diff": avg(latest_form[home], 5, 0.5) - avg(latest_form[away], 5, 0.5),
            "form10_diff": avg(latest_form[home], 10, 0.5) - avg(latest_form[away], 10, 0.5),
            "gf5_home": avg(latest_gf[home], 5, 1.2),
            "gf5_away": avg(latest_gf[away], 5, 1.2),
            "ga5_home": avg(latest_ga[home], 5, 1.2),
            "ga5_away": avg(latest_ga[away], 5, 1.2),
            "attack_home": avg(latest_attack[home], 20, 1.3),
            "attack_away": avg(latest_attack[away], 20, 1.3),
            "defense_home": avg(latest_defense[home], 20, 1.3),
            "defense_away": avg(latest_defense[away], 20, 1.3),
            "rest_diff": (
                ((pd.to_datetime(date_iso).date() - last_dates[home]).days if home in last_dates else 14)
                - ((pd.to_datetime(date_iso).date() - last_dates[away]).days if away in last_dates else 14)
            ),
            "host_home": int(bool(meta.loc[home, "is_host"])) if home in meta.index else 0,
            "host_away": int(bool(meta.loc[away, "is_host"])) if away in meta.index else 0,
            "same_confederation": int(
                home in meta.index and away in meta.index and
                meta.loc[home, "confederation"] == meta.loc[away, "confederation"]
            ),
            "neutral": int(bool(getattr(fx, "neutral", True))),
            "stage": getattr(fx, "stage", "group"),
            "group": getattr(fx, "group", None),
            "venue": getattr(fx, "venue", None),
        }
        rows.append(feat)
    return pd.DataFrame(rows)
