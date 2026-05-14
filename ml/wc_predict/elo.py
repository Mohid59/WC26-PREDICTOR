"""Elo ratings updated chronologically across historical results.

We use a standard Elo update with a goal-difference multiplier (similar to
World Football Elo / FiveThirtyEight style). Ratings are produced as a time
series so that, for any historical match, we can recover the rating that
existed BEFORE that match — this is essential to avoid feature leakage.
"""
from __future__ import annotations
import math
import pandas as pd
from collections import defaultdict
from dataclasses import dataclass, field


HOME_ADV_ELO = 60.0
K_BASE = 30.0
TOURNAMENT_K_MULT = {
    "friendly": 1.0,
    "qualifier": 1.25,
    "uefa_nations": 1.1,
    "copa_america": 1.4,
    "world_cup": 1.6,
}


def expected_score(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def _gd_multiplier(goal_diff: int) -> float:
    g = abs(goal_diff)
    if g <= 1:
        return 1.0
    if g == 2:
        return 1.5
    return (11 + g) / 8.0


@dataclass
class EloHistory:
    """Captures (rating_before_match) for every team-date pair."""
    final_ratings: dict[str, float] = field(default_factory=dict)
    pre_match_lookup: dict[tuple[str, str], tuple[float, float]] = field(default_factory=dict)
    # team -> sorted list of (date_iso, rating_after)
    history: dict[str, list[tuple[str, float]]] = field(default_factory=lambda: defaultdict(list))

    def rating_on_or_before(self, team: str, date_iso: str, default: float = 1500.0) -> float:
        ts = self.history.get(team, [])
        if not ts:
            return self.final_ratings.get(team, default)
        # binary search
        lo, hi = 0, len(ts) - 1
        ans = default
        while lo <= hi:
            mid = (lo + hi) // 2
            if ts[mid][0] <= date_iso:
                ans = ts[mid][1]
                lo = mid + 1
            else:
                hi = mid - 1
        return ans


def build_elo_history(results: pd.DataFrame, seed_ratings: dict[str, float] | None = None) -> EloHistory:
    seed_ratings = dict(seed_ratings or {})
    ratings: dict[str, float] = defaultdict(lambda: 1500.0)
    for k, v in seed_ratings.items():
        ratings[k] = float(v)
    hist = EloHistory()
    for row in results.itertuples(index=False):
        home, away = row.home, row.away
        ra = ratings[home]
        rb = ratings[away]
        date_iso = str(row.date)
        hist.pre_match_lookup[(date_iso, f"{home}|{away}")] = (ra, rb)
        # Update
        gd = int(row.home_goals) - int(row.away_goals)
        result = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)
        adv = 0.0 if bool(row.neutral) else HOME_ADV_ELO
        exp_h = expected_score(ra + adv, rb)
        k = K_BASE * TOURNAMENT_K_MULT.get(str(row.tournament), 1.0) * _gd_multiplier(gd)
        delta = k * (result - exp_h)
        ratings[home] = ra + delta
        ratings[away] = rb - delta
        hist.history[home].append((date_iso, ratings[home]))
        hist.history[away].append((date_iso, ratings[away]))
    hist.final_ratings = dict(ratings)
    return hist
