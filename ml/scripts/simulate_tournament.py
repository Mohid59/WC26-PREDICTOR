"""Run Monte Carlo tournament simulation and save artefacts for the UI."""
from __future__ import annotations
import os
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import (
    ensure_dirs, FIXTURES_CSV, TEAMS_CSV, MODEL_PATH, SIMULATION_JSON,
    ELO_PATH, RESULTS_CSV
)
from wc_predict.data import load_fixtures, load_teams, load_results
from wc_predict.elo import build_elo_history
from wc_predict.model import ModelArtifacts
from wc_predict.simulator import run_simulation, MatchPrediction


def main() -> int:
    ensure_dirs()
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sims", type=int, default=int(os.environ.get("WC26_N_SIMULATIONS", 5000)))
    ap.add_argument("--seed", type=int, default=int(os.environ.get("WC26_SEED", 42)))
    args = ap.parse_args()

    fx = load_fixtures(FIXTURES_CSV)
    teams = load_teams(TEAMS_CSV)
    results = load_results(RESULTS_CSV)
    seed_ratings = dict(zip(teams["code"], teams["elo_seed"]))
    elo_hist = build_elo_history(results, seed_ratings=seed_ratings)
    ELO_PATH.write_text(json.dumps(elo_hist.final_ratings, indent=2), encoding="utf-8")

    preds_path = Path(SIMULATION_JSON).parent / "predictions.json"
    if not preds_path.exists():
        print("[simulate_tournament] predictions.json missing; run predict_fixtures.py first", file=sys.stderr)
        return 1
    pred_data = json.loads(preds_path.read_text(encoding="utf-8"))
    mps: list[MatchPrediction] = []
    for p in pred_data["items"]:
        mps.append(MatchPrediction(
            match_id=p["match_id"], home=p["home"], away=p["away"],
            p_home=p["p_home"], p_draw=p["p_draw"], p_away=p["p_away"],
            xg_home=p["xg_home"], xg_away=p["xg_away"],
            stage=p["stage"], group=p.get("group"), date=p["date"],
        ))

    # Derive groups from fixtures
    groups: dict[str, list[str]] = defaultdict(list)
    for r in fx[fx["stage"] == "group"].itertuples(index=False):
        if r.home not in groups[r.group]:
            groups[r.group].append(r.home)
        if r.away not in groups[r.group]:
            groups[r.group].append(r.away)

    result = run_simulation(
        groups=dict(groups), fixtures=fx, predictions=mps,
        final_elo=elo_hist.final_ratings,
        n_sims=args.n_sims, seed=args.seed,
    )
    payload = {
        "n_sims": result.n_sims,
        "seed": result.seed,
        "round_probs": result.round_probs,
        "group_finish": result.group_finish,
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    SIMULATION_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[simulate_tournament] {args.n_sims} simulations -> {SIMULATION_JSON}")
    top = sorted(result.round_probs.items(), key=lambda kv: -kv[1]["winner"])[:8]
    print("[simulate_tournament] Top winner probabilities:")
    for t, probs in top:
        print(f"  {t}: winner={probs['winner']:.3f}  sf={probs['sf']:.3f}  r16={probs['r16']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
