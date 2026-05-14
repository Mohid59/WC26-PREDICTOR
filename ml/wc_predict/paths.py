"""Centralized filesystem paths so scripts and tests agree."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
PUBLIC_DATA_DIR = ROOT / "public" / "data"

RESULTS_CSV = RAW_DIR / "results.csv"
FIXTURES_CSV = RAW_DIR / "fixtures_wc2026.csv"
TEAMS_CSV = RAW_DIR / "teams_wc2026.csv"
FEATURES_CSV = PROCESSED_DIR / "features.csv"
MODEL_PATH = MODELS_DIR / "model.joblib"
ELO_PATH = MODELS_DIR / "elo_ratings.json"
METRICS_PATH = REPORTS_DIR / "metrics.json"
PREDICTIONS_JSON = PUBLIC_DATA_DIR / "predictions.json"
FIXTURES_JSON = PUBLIC_DATA_DIR / "fixtures.json"
TEAMS_JSON = PUBLIC_DATA_DIR / "teams.json"
SIMULATION_JSON = PUBLIC_DATA_DIR / "simulation.json"
MODEL_INFO_JSON = PUBLIC_DATA_DIR / "model_info.json"
DATA_STATUS_JSON = PUBLIC_DATA_DIR / "data_status.json"


def ensure_dirs() -> None:
    for d in (RAW_DIR, PROCESSED_DIR, MODELS_DIR, REPORTS_DIR, PUBLIC_DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)
