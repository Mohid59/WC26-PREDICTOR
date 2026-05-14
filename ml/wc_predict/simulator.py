"""Monte Carlo tournament simulator for WC26.

Pipeline:
  1. From group fixtures + match probability/scoreline distribution, sample
     a goal-for / goal-against pair per group match via independent Poisson.
  2. Apply FIFA tiebreakers: points > GD > GF > head-to-head > drawing of lots
     (deterministic via stable hash, documented in README).
  3. Top 2 from each group + best 8 third-placed teams advance to Round of 32.
  4. Knockout: simulate via xG-based scoreline; if draw, settle via shootout
     with team-strength-weighted Bernoulli.
  5. Aggregate over N simulations to produce per-team round probabilities.
"""
from __future__ import annotations
import math
import json
import random
import hashlib
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional
import numpy as np
import pandas as pd

ROUNDS = ["group", "r32", "r16", "qf", "sf", "final", "winner"]


@dataclass
class MatchPrediction:
    match_id: str
    home: str
    away: str
    p_home: float
    p_draw: float
    p_away: float
    xg_home: float
    xg_away: float
    stage: str
    group: Optional[str] = None
    date: Optional[str] = None


@dataclass
class SimulationResult:
    n_sims: int
    seed: int
    round_probs: dict[str, dict[str, float]]  # team -> {round: prob}
    group_finish: dict[str, dict[str, dict[str, float]]]  # group -> team -> {pos: prob}
    most_likely_path: dict[str, list[str]]  # team -> sequence of opponents (one rep)


def _sample_poisson(lam: float, rng: random.Random) -> int:
    L = math.exp(-lam); k = 0; p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def _shootout_winner(home: str, away: str, ratings: dict[str, float], rng: random.Random) -> str:
    """Team-strength-weighted Bernoulli per kick, first-to-mistake-loses approximation."""
    ra = ratings.get(home, 1500.0)
    rb = ratings.get(away, 1500.0)
    p_home_score = 1.0 / (1.0 + 10 ** ((rb - ra) / 800.0))
    p_home_score = 0.55 + (p_home_score - 0.5) * 0.3  # squash to plausible shootout window
    p_away_score = 1 - (p_home_score - 0.5)
    p_away_score = 0.55 + (p_away_score - 0.5) * 0.3
    h_s = a_s = 0
    for _ in range(5):
        if rng.random() < p_home_score: h_s += 1
        if rng.random() < p_away_score: a_s += 1
    while h_s == a_s:
        if rng.random() < p_home_score: h_s += 1
        if rng.random() < p_away_score: a_s += 1
    return home if h_s > a_s else away


def _stable_tiebreak(team_codes: list[str], seed: int) -> list[str]:
    """Deterministic drawing-of-lots fallback (documented)."""
    return sorted(team_codes, key=lambda t: hashlib.md5(f"{seed}:{t}".encode()).hexdigest())


def simulate_group(
    group: str,
    teams: list[str],
    match_preds: list[MatchPrediction],
    seed: int,
    rng: random.Random,
) -> list[tuple[str, int, int, int]]:
    """Return ordered standings: (team, points, goal_diff, goals_for)."""
    pts = {t: 0 for t in teams}
    gf = {t: 0 for t in teams}
    ga = {t: 0 for t in teams}
    h2h_pts: dict[tuple[str, str], int] = defaultdict(int)
    h2h_gd: dict[tuple[str, str], int] = defaultdict(int)
    for mp in match_preds:
        h, a = mp.home, mp.away
        if h not in pts or a not in pts:
            continue
        gh = _sample_poisson(mp.xg_home, rng)
        ga_ = _sample_poisson(mp.xg_away, rng)
        gf[h] += gh; ga[h] += ga_
        gf[a] += ga_; ga[a] += gh
        h2h_gd[(h, a)] += gh - ga_
        h2h_gd[(a, h)] += ga_ - gh
        if gh > ga_:
            pts[h] += 3
            h2h_pts[(h, a)] += 3
        elif gh == ga_:
            pts[h] += 1; pts[a] += 1
            h2h_pts[(h, a)] += 1; h2h_pts[(a, h)] += 1
        else:
            pts[a] += 3
            h2h_pts[(a, h)] += 3
    # Sort: points DESC, GD DESC, GF DESC, then deterministic lot
    def key(t):
        return (-pts[t], -(gf[t] - ga[t]), -gf[t])
    ordered = sorted(teams, key=key)
    # Resolve exact ties via h2h then deterministic lot
    result: list[tuple[str, int, int, int]] = []
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and key(ordered[i]) == key(ordered[j]):
            j += 1
        chunk = ordered[i:j]
        if len(chunk) > 1:
            chunk = sorted(chunk, key=lambda t: (
                -sum(h2h_pts[(t, o)] for o in chunk if o != t),
                -sum(h2h_gd[(t, o)] for o in chunk if o != t),
            ))
            # final lot
            grouped: dict[tuple, list[str]] = defaultdict(list)
            for t in chunk:
                grouped[(
                    -sum(h2h_pts[(t, o)] for o in chunk if o != t),
                    -sum(h2h_gd[(t, o)] for o in chunk if o != t),
                )].append(t)
            chunk = []
            for k in sorted(grouped.keys()):
                if len(grouped[k]) > 1:
                    chunk.extend(_stable_tiebreak(grouped[k], seed))
                else:
                    chunk.extend(grouped[k])
        for t in chunk:
            result.append((t, pts[t], gf[t] - ga[t], gf[t]))
        i = j
    return result


def _knockout(
    home: str, away: str,
    base_lookup: dict[tuple[str, str], MatchPrediction],
    ratings: dict[str, float],
    rng: random.Random,
) -> str:
    mp = base_lookup.get((home, away)) or base_lookup.get((away, home))
    if mp is None:
        # synthesize via ratings
        ra = ratings.get(home, 1500.0)
        rb = ratings.get(away, 1500.0)
        diff = (ra - rb) / 400.0
        xh = max(0.2, 1.3 * math.exp(0.35 * diff))
        xa = max(0.2, 1.3 * math.exp(-0.35 * diff))
    else:
        xh, xa = mp.xg_home, mp.xg_away
        if mp.home != home:
            xh, xa = xa, xh
    gh = _sample_poisson(xh, rng)
    ga = _sample_poisson(xa, rng)
    if gh > ga:
        return home
    if ga > gh:
        return away
    return _shootout_winner(home, away, ratings, rng)


def run_simulation(
    groups: dict[str, list[str]],
    fixtures: pd.DataFrame,
    predictions: list[MatchPrediction],
    final_elo: dict[str, float],
    n_sims: int = 10_000,
    seed: int = 42,
) -> SimulationResult:
    rng = random.Random(seed)
    by_group: dict[str, list[MatchPrediction]] = defaultdict(list)
    base_lookup: dict[tuple[str, str], MatchPrediction] = {}
    for p in predictions:
        base_lookup[(p.home, p.away)] = p
        if p.stage == "group" and p.group:
            by_group[p.group].append(p)

    # Counters
    round_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    group_pos: dict[str, dict[str, dict[int, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    sample_path: dict[str, list[str]] = {}

    for s in range(n_sims):
        local_rng = random.Random(seed * 1_000_003 + s)
        standings: dict[str, list[tuple[str, int, int, int]]] = {}
        for g, teams in groups.items():
            standings[g] = simulate_group(g, teams, by_group.get(g, []), seed=seed + s, rng=local_rng)
            for pos, (team, *_rest) in enumerate(standings[g], start=1):
                group_pos[g][team][pos] += 1
                if pos <= 2:
                    round_counts["r32"][team] += 1

        # Best 8 third-placed teams: rank by points, GD, GF
        thirds = []
        for g, ord_ in standings.items():
            if len(ord_) >= 3:
                t, pts, gd, gf = ord_[2]
                thirds.append((t, pts, gd, gf, g))
        thirds.sort(key=lambda x: (-x[1], -x[2], -x[3]))
        for t, *_ in thirds[:8]:
            round_counts["r32"][t] += 1

        # Build R32 bracket — simple seeded pairing
        r32_teams = []
        for g in sorted(groups.keys()):
            if len(standings[g]) >= 1:
                r32_teams.append(standings[g][0][0])
        for g in sorted(groups.keys()):
            if len(standings[g]) >= 2:
                r32_teams.append(standings[g][1][0])
        r32_teams.extend([t for t, *_ in thirds[:8]])
        # Pad if short
        while len(r32_teams) < 32:
            r32_teams.append(r32_teams[-1])
        local_rng.shuffle(r32_teams)
        r32_teams = r32_teams[:32]

        round_teams = r32_teams
        for round_name in ("r16", "qf", "sf", "final"):
            winners = []
            for i in range(0, len(round_teams), 2):
                a, b = round_teams[i], round_teams[i + 1]
                w = _knockout(a, b, base_lookup, final_elo, local_rng)
                winners.append(w)
                round_counts[round_name][w] += 1
            round_teams = winners
        if round_teams:
            round_counts["winner"][round_teams[0]] += 1
            if round_teams[0] not in sample_path:
                sample_path[round_teams[0]] = [t for t in r32_teams]

    # Convert to probabilities
    round_probs: dict[str, dict[str, float]] = {}
    all_teams = sorted({t for ts in groups.values() for t in ts})
    for t in all_teams:
        round_probs[t] = {
            "group_play": 1.0,
            "r32": round_counts["r32"].get(t, 0) / n_sims,
            "r16": round_counts["r16"].get(t, 0) / n_sims,
            "qf": round_counts["qf"].get(t, 0) / n_sims,
            "sf": round_counts["sf"].get(t, 0) / n_sims,
            "final": round_counts["final"].get(t, 0) / n_sims,
            "winner": round_counts["winner"].get(t, 0) / n_sims,
        }

    group_finish: dict[str, dict[str, dict[str, float]]] = {}
    for g, teams_in_group in group_pos.items():
        group_finish[g] = {}
        for t, pos_counts in teams_in_group.items():
            group_finish[g][t] = {str(p): pos_counts.get(p, 0) / n_sims for p in (1, 2, 3, 4)}

    return SimulationResult(
        n_sims=n_sims,
        seed=seed,
        round_probs=round_probs,
        group_finish=group_finish,
        most_likely_path=sample_path,
    )
