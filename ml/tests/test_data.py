"""Data loading sanity tests."""
import pandas as pd
import pytest
from pathlib import Path
from wc_predict.data import load_results, load_teams, load_fixtures


def test_results_missing_column_raises(tmp_path: Path):
    p = tmp_path / "bad.csv"
    p.write_text("date,home,away,home_goals,away_goals,tournament\n2024-01-01,A,B,1,0,friendly\n")
    with pytest.raises(ValueError):
        load_results(p)


def test_results_loads_minimal(tmp_path: Path):
    p = tmp_path / "ok.csv"
    p.write_text(
        "date,home,away,home_goals,away_goals,tournament,neutral\n"
        "2024-01-01,A,B,2,1,friendly,1\n"
        "2024-02-01,B,C,0,2,friendly,1\n"
    )
    df = load_results(p)
    assert len(df) == 2
    assert df.iloc[0]["home_goals"] == 2


def test_teams_loads(tmp_path: Path):
    p = tmp_path / "t.csv"
    p.write_text(
        "code,name,confederation,pot,is_host,elo_seed\n"
        "USA,United States,CONCACAF,1,1,1800\n"
    )
    df = load_teams(p)
    assert df.iloc[0]["is_host"]
