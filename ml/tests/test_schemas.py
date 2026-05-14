import pytest
from datetime import date
from wc_predict.schemas import ResultRecord, FixtureRecord, TeamRecord, PredictionRecord


def test_result_validates():
    r = ResultRecord(date=date(2024, 1, 1), home="USA", away="MEX", home_goals=2, away_goals=1)
    assert r.home == "USA" and r.home_goals == 2


def test_result_rejects_negative_goals():
    with pytest.raises(Exception):
        ResultRecord(date=date(2024, 1, 1), home="A", away="B", home_goals=-1, away_goals=0)


def test_fixture_requires_stage():
    fx = FixtureRecord(match_id="G001", date=date(2026, 6, 11), stage="group",
                       group="A", home="USA", away="MEX")
    assert fx.stage == "group"


def test_team_record():
    t = TeamRecord(code="USA", name="United States", confederation="CONCACAF", is_host=True)
    assert t.is_host


def test_prediction_probs_sum_to_one():
    p = PredictionRecord(
        match_id="G001", p_home=0.5, p_draw=0.3, p_away=0.2,
        xg_home=1.5, xg_away=0.9, likely_scores=[(1, 0, 0.12)],
        confidence=0.4, top_features=[("elo_diff", 1.2)],
        model_version="v0", generated_at="2026-05-01T00:00:00Z",
    )
    assert abs(p.p_home + p.p_draw + p.p_away - 1.0) < 1e-3


def test_prediction_rejects_bad_sum():
    with pytest.raises(Exception):
        PredictionRecord(
            match_id="X", p_home=0.6, p_draw=0.6, p_away=0.2,
            xg_home=1, xg_away=1, likely_scores=[],
            confidence=0.5, top_features=[],
            model_version="v0", generated_at="2026-05-01T00:00:00Z",
        )
