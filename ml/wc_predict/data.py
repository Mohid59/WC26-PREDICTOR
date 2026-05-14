"""Data loading and validation. Errors loudly when sources are malformed."""
from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Any
from .schemas import TeamRecord, ResultRecord, FixtureRecord


REQUIRED_RESULT_COLS = {"date", "home", "away", "home_goals", "away_goals", "tournament", "neutral"}
REQUIRED_TEAM_COLS = {"code", "name", "confederation", "pot", "is_host", "elo_seed"}
REQUIRED_FIXTURE_COLS = {"match_id", "date", "stage", "home", "away"}


def _require_cols(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{name}: missing columns {sorted(missing)}")


def load_results(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _require_cols(df, REQUIRED_RESULT_COLS, "results")
    n_in = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df = df.dropna(subset=["date", "home", "away", "home_goals", "away_goals"]).copy()
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)
    df["tournament"] = df["tournament"].fillna("friendly").astype(str)
    # neutral may arrive as bool/int/"TRUE"/"FALSE" — normalise robustly
    df["neutral"] = df["neutral"].map(
        lambda v: bool(v) if isinstance(v, (bool,)) else
        (str(v).strip().lower() in ("1", "true", "t", "yes"))
    )
    n_drop = n_in - len(df)
    if n_drop:
        print(f"[data.load_results] dropped {n_drop} malformed rows")
    for rec in df.head(5).to_dict("records"):
        ResultRecord(**{**rec, "neutral": bool(rec["neutral"])})
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_teams(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _require_cols(df, REQUIRED_TEAM_COLS, "teams")
    df["is_host"] = df["is_host"].astype(int).astype(bool)
    df["pot"] = df["pot"].astype(int)
    df["elo_seed"] = df["elo_seed"].astype(float)
    for rec in df.head(5).to_dict("records"):
        TeamRecord(**{**rec, "is_host": bool(rec["is_host"])})
    return df


def load_fixtures(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    _require_cols(df, REQUIRED_FIXTURE_COLS, "fixtures")
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.date
    if "neutral" in df.columns:
        df["neutral"] = df["neutral"].astype(int).astype(bool)
    else:
        df["neutral"] = True
    for rec in df.head(5).to_dict("records"):
        FixtureRecord(**{**rec, "neutral": bool(rec.get("neutral", True))})
    return df.sort_values(["date", "match_id"]).reset_index(drop=True)
