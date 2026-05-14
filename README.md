# WC26 Predictor

A production-quality web app that predicts FIFA World Cup 2026 match outcomes with
calibrated probabilities, expected goals, likely scorelines, model explanations, and a
Monte Carlo tournament simulation.

> **Disclaimer.** Predictions are probabilistic estimates from a model trained on
> historical international match data. They are **not** guarantees and **not** betting
> advice.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS |
| API | Next.js route handlers; zod for body validation |
| ML pipeline | Python 3.11 · pandas · scikit-learn · scipy · pydantic |
| Modelling | Calibrated multinomial logistic + Poisson regressors; Elo ratings |
| Simulation | Configurable Monte Carlo with seeded RNG |
| Tests | pytest (ML) · Vitest + Testing Library (frontend) |

## Quick start

```bash
# 1. Install dependencies (Python and Node)
npm install
npm run ml:install            # installs ml/requirements.txt

# 2. Generate model artefacts (fetches historical data, trains, simulates)
npm run ml:pipeline           # ~30s end-to-end

# 3. Run the dev server
npm run dev                   # http://localhost:3000

# 4. Run tests
npm run ml:test               # pytest (Python)
npm test                      # vitest (frontend)
npm run typecheck             # strict tsc
npm run build                 # next build (static)
```

## Project structure

```
app/                     Next.js App Router
  page.tsx               Dashboard
  fixtures/              Fixtures + predictions index
  match/[matchId]/       Match detail (probabilities, xG, scorelines, features)
  bracket/               Tournament bracket simulation
  metrics/               Model metrics + calibration + confusion matrix
  data-status/           Data freshness, sources, refresh instructions
  api/                   GET /api/{fixtures,teams,predictions,simulations,model/*,data-status}
                         POST /api/simulations/run (re-run simulator)
                         POST /api/admin/refresh-data (local-only or token-gated)
  components/            ProbBar, MatchCard, SampleDataBanner
  lib/                   Artifact loaders + shared types
ml/
  wc_predict/            Library: data, features, elo, model, simulator, schemas
  scripts/               fetch_results, fetch_fixtures, build_features, train_model,
                         evaluate_model, predict_fixtures, simulate_tournament, run_pipeline
  tests/                 pytest: schemas, data, elo, no-leakage, model, simulator
data/                    raw + processed CSVs (gitignored)
models/                  Trained model.joblib + elo_ratings.json (gitignored)
reports/                 Metrics JSON (gitignored)
public/data/             JSON artefacts consumed by the frontend
                         predictions.json, simulation.json, fixtures.json, teams.json,
                         model_info.json, data_status.json
```

## How the pipeline works

```
fetch_results.py  ── tries martj42/international_results (CC0 public dataset);
                     falls back to a synthetic Elo→Poisson seed and writes
                     public/data/data_status.json to flag the source.
fetch_fixtures.py ── writes sample WC26 teams + group fixtures (48 teams,
                     12 groups, 72 matches, clearly labelled SAMPLE).
build_features.py ── computes per-match features with strict no-leakage:
                     ratings as of (match_date - 1 day), rolling form/goals
                     populated only from prior matches.
train_model.py    ── time-aware 85/15 split; multinomial logistic + Standard
                     scaler, wrapped in CalibratedClassifierCV (isotonic, TS
                     CV). Poisson regressors for home_goals and away_goals.
                     Saves model.joblib, reports/metrics.json, model_info.json.
predict_fixtures.py ── runs the model over WC26 fixtures, emits
                     public/data/predictions.json.
simulate_tournament.py ── Monte Carlo over the group + knockout draw using
                     predicted xG; FIFA tiebreakers (points > GD > GF > h2h),
                     deterministic lot fallback (stable md5 of seed:team).
                     Knockout shootouts via team-strength-weighted Bernoulli.
                     Configurable --n-sims and --seed. Writes simulation.json.
```

## Modelling notes

- **Features.** elo_diff, elo_home, elo_away, form5/10 diff, gf5/ga5 per side,
  attack/defense rolling means (last 20 matches), rest-day differential, host indicator,
  same-confederation flag, neutral-site flag. All computed pre-match — verified by
  `ml/tests/test_no_leakage.py`.
- **Calibration.** Isotonic regression on top of the logistic base model, applied via
  `CalibratedClassifierCV` with time-series cross-validation. Calibration table is on
  the Model Metrics page.
- **Baseline.** Holdout log-loss is compared against the empirical class-frequency
  baseline; the page surfaces both.
- **Goal model.** Two `PoissonRegressor`s on the same features, used as λ for an
  independent-Poisson scoreline distribution (good enough for top-5 most likely scores;
  not Dixon-Coles dependency-adjusted).
- **Explanation.** "Top features" on the match page are linear contributions from the
  pre-calibration logistic component (standardised feature × coefficient for the
  predicted class). Directional signal, not a causal claim.

## Tournament simulation

- 5,000 simulations by default (override with `WC26_N_SIMULATIONS` or `--n-sims`).
- Default seed 42 — reproducible across runs (verified in `test_simulator.py`).
- Group standings use **points → goal difference → goals for → head-to-head → drawing
  of lots**. The drawing-of-lots step is deterministic via stable hashing of the
  `seed:team` pair so that identical inputs reproduce identical outputs.
- Knockout draws or shootouts after extra time use a strength-weighted Bernoulli per
  kick (clamped to a plausible 0.55–0.75 conversion window).

## Data sources

| Source | What it provides | Status |
|---|---|---|
| [martj42/international_results](https://github.com/martj42/international_results) | International match history (CC0) | Used when network is available |
| Bundled WC26 fixtures | 48-team draw, 72 group matches | **Sample** — replace via your own fixture connector |
| Bundled WC26 teams | Confederation + pot + seed Elo | **Sample** — projected qualifiers |

The Data page shows the current sources and last refresh time. When sample data is in
use, a persistent banner appears at the top of every page.

## Testing

```bash
npm run ml:test        # 20 pytest cases (schemas, data, elo, no-leakage, model, simulator)
npm test               # 5 vitest cases (ProbBar, artifact helpers)
npm run typecheck      # strict TypeScript
npm run build          # next build (verifies SSG of all 88 routes)
```

The no-leakage suite is the load-bearing test: it asserts that the ELO rating used as
a feature for match M equals the rating computed from matches strictly before M.

## Environment

See `.env.example`. Useful knobs:

- `WC26_USE_SAMPLE_DATA=true` — forces sample-data mode even when network is reachable.
- `WC26_N_SIMULATIONS=10000` — override default Monte Carlo run size.
- `WC26_SEED=42` — RNG seed used by the simulator.
- `ADMIN_REFRESH_TOKEN` — token required by `POST /api/admin/refresh-data` when the
  request does not come from localhost.

## Known limitations

- The WC26 fixture list and groups are **sample/projected** — the included data is
  plausible but not authoritative. Replace `ml/scripts/fetch_fixtures.py` with a
  connector to FIFA's official schedule for production use.
- The synthetic-data fallback for the historical record is clearly weaker training
  signal than the real martj42 dataset; the UI flags the source on every page.
- XGBoost/LightGBM are not used; the spec calls them "optional" and we kept the
  install footprint Windows-friendly. Adding them is straightforward — register an
  alternative classifier in `ml/wc_predict/model.py` and re-run `npm run ml:train`.
- Penalty-shootout modelling is a simple strength-weighted Bernoulli, not a per-team
  shootout-history model.
- No Playwright e2e suite (Vitest covers frontend utilities + components; pytest
  covers ML).
- No CI workflow file in this pass — GitHub Actions setup is straightforward (`npm
  run typecheck && npm test && npm run ml:test && npm run build`).
