"""Pydantic schemas for validation at data boundaries."""
from __future__ import annotations
from datetime import date as Date
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

Stage = Literal["group", "r32", "r16", "qf", "sf", "third", "final"]
Confederation = Literal["UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"]


class TeamRecord(BaseModel):
    code: str = Field(min_length=2, max_length=3)
    name: str
    confederation: Confederation
    is_host: bool = False
    elo_seed: float = 1500.0


class ResultRecord(BaseModel):
    date: Date
    home: str
    away: str
    home_goals: int = Field(ge=0)
    away_goals: int = Field(ge=0)
    tournament: str = "friendly"
    neutral: bool = False

    @field_validator("home", "away")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("team name required")
        return v.strip()


class FixtureRecord(BaseModel):
    match_id: str
    date: Date
    kickoff: Optional[str] = None
    stage: Stage
    group: Optional[str] = None
    venue: Optional[str] = None
    home: str
    away: str
    neutral: bool = True


class PredictionRecord(BaseModel):
    match_id: str
    p_home: float = Field(ge=0, le=1)
    p_draw: float = Field(ge=0, le=1)
    p_away: float = Field(ge=0, le=1)
    xg_home: float = Field(ge=0)
    xg_away: float = Field(ge=0)
    likely_scores: list[tuple[int, int, float]]
    confidence: float = Field(ge=0, le=1)
    top_features: list[tuple[str, float]]
    model_version: str
    generated_at: str

    @field_validator("p_away")
    @classmethod
    def probs_sum_to_one(cls, v: float, info) -> float:
        ph = info.data.get("p_home", 0)
        pd = info.data.get("p_draw", 0)
        s = ph + pd + v
        if abs(s - 1.0) > 1e-3:
            raise ValueError(f"probabilities must sum to 1.0, got {s}")
        return v
