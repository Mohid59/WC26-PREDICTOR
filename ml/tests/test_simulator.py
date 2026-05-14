"""Simulator tests: group ranking + advancement + reproducibility."""
import random
from wc_predict.simulator import simulate_group, run_simulation, MatchPrediction
import pandas as pd


def test_group_tiebreak_points_then_gd():
    teams = ["A", "B", "C", "D"]
    # craft predictions that produce a clear order via xG
    preds = [
        MatchPrediction("m1", "A", "B", 0.6, 0.2, 0.2, 2.0, 0.3, "group", "G"),
        MatchPrediction("m2", "A", "C", 0.6, 0.2, 0.2, 2.0, 0.3, "group", "G"),
        MatchPrediction("m3", "A", "D", 0.6, 0.2, 0.2, 2.0, 0.3, "group", "G"),
        MatchPrediction("m4", "B", "C", 0.4, 0.3, 0.3, 1.4, 1.0, "group", "G"),
        MatchPrediction("m5", "B", "D", 0.5, 0.3, 0.2, 1.6, 0.7, "group", "G"),
        MatchPrediction("m6", "C", "D", 0.45, 0.3, 0.25, 1.3, 0.9, "group", "G"),
    ]
    rng = random.Random(0)
    standings = simulate_group("G", teams, preds, seed=0, rng=rng)
    names = [t for t, *_ in standings]
    assert names[0] == "A"  # A should win


def test_simulation_winner_prob_sums_to_one():
    teams_by_group = {"A": ["A1", "A2", "A3", "A4"], "B": ["B1", "B2", "B3", "B4"]}
    preds = []
    for g, teams in teams_by_group.items():
        for i in range(4):
            for j in range(i + 1, 4):
                preds.append(MatchPrediction(
                    match_id=f"{g}-{i}{j}", home=teams[i], away=teams[j],
                    p_home=0.4, p_draw=0.3, p_away=0.3,
                    xg_home=1.3, xg_away=1.1, stage="group", group=g,
                ))
    fx = pd.DataFrame([
        {"match_id": p.match_id, "date": "2026-06-11", "stage": "group",
         "group": p.group, "home": p.home, "away": p.away, "neutral": True}
        for p in preds
    ])
    res = run_simulation(
        groups=teams_by_group, fixtures=fx, predictions=preds,
        final_elo={t: 1500.0 for ts in teams_by_group.values() for t in ts},
        n_sims=200, seed=1,
    )
    total_winner = sum(p["winner"] for p in res.round_probs.values())
    assert abs(total_winner - 1.0) < 0.01


def test_simulation_reproducible():
    teams_by_group = {"A": ["X1", "X2", "X3", "X4"], "B": ["Y1", "Y2", "Y3", "Y4"]}
    preds = [
        MatchPrediction(f"m{i}", a, b, 0.4, 0.3, 0.3, 1.4, 1.2, "group", g)
        for g, teams in teams_by_group.items()
        for i, (a, b) in enumerate([(teams[0], teams[1]), (teams[2], teams[3]),
                                     (teams[0], teams[2]), (teams[1], teams[3]),
                                     (teams[0], teams[3]), (teams[1], teams[2])])
    ]
    fx = pd.DataFrame([{"match_id": p.match_id, "date": "2026-06-11", "stage": "group",
                        "group": p.group, "home": p.home, "away": p.away, "neutral": True}
                       for p in preds])
    a = run_simulation(teams_by_group, fx, preds, {t: 1500.0 for ts in teams_by_group.values() for t in ts}, n_sims=100, seed=42)
    b = run_simulation(teams_by_group, fx, preds, {t: 1500.0 for ts in teams_by_group.values() for t in ts}, n_sims=100, seed=42)
    assert a.round_probs == b.round_probs
