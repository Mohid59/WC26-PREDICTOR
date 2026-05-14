"""Sync the committed FIFA World Cup 2026 schedule artifacts.

FIFA's public schedule page is rendered by a client app, so this parser reads the
Wikipedia match pages that transclude per-match FIFA match-centre references.
The generated artifacts are static and are checked into the project for the app.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import (  # noqa: E402
    DATA_STATUS_JSON,
    FIXTURES_CSV,
    FIXTURES_JSON,
    TEAMS_CSV,
    TEAMS_JSON,
    ensure_dirs,
)

WIKI_RAW = "https://en.wikipedia.org/w/index.php?title={title}&action=raw"
OFFICIAL_SOURCE_URL = (
    "https://www.fifa.com/en/tournaments/mens/worldcup/"
    "canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums"
)
HEADERS = {"User-Agent": "wc26-predictor schedule sync (local project)"}


@dataclass(frozen=True)
class TeamSeed:
    code: str
    name: str
    confederation: str
    pot: int
    is_host: bool
    elo_seed: float


TEAMS: list[TeamSeed] = [
    TeamSeed("MEX", "Mexico", "CONCACAF", 1, True, 1810),
    TeamSeed("RSA", "South Africa", "CAF", 3, False, 1650),
    TeamSeed("KOR", "Korea Republic", "AFC", 2, False, 1780),
    TeamSeed("CZE", "Czechia", "UEFA", 4, False, 1760),
    TeamSeed("CAN", "Canada", "CONCACAF", 1, True, 1740),
    TeamSeed("BIH", "Bosnia and Herzegovina", "UEFA", 4, False, 1690),
    TeamSeed("QAT", "Qatar", "AFC", 3, False, 1700),
    TeamSeed("SUI", "Switzerland", "UEFA", 2, False, 1820),
    TeamSeed("BRA", "Brazil", "CONMEBOL", 1, False, 2030),
    TeamSeed("MAR", "Morocco", "CAF", 2, False, 1830),
    TeamSeed("HAI", "Haiti", "CONCACAF", 4, False, 1500),
    TeamSeed("SCO", "Scotland", "UEFA", 3, False, 1750),
    TeamSeed("USA", "United States", "CONCACAF", 1, True, 1810),
    TeamSeed("PAR", "Paraguay", "CONMEBOL", 3, False, 1700),
    TeamSeed("AUS", "Australia", "AFC", 2, False, 1770),
    TeamSeed("TUR", "Turkiye", "UEFA", 3, False, 1770),
    TeamSeed("GER", "Germany", "UEFA", 1, False, 1940),
    TeamSeed("CUW", "Curacao", "CONCACAF", 4, False, 1500),
    TeamSeed("CIV", "Cote d'Ivoire", "CAF", 4, False, 1710),
    TeamSeed("ECU", "Ecuador", "CONMEBOL", 3, False, 1740),
    TeamSeed("NED", "Netherlands", "UEFA", 1, False, 1960),
    TeamSeed("JPN", "Japan", "AFC", 2, False, 1820),
    TeamSeed("SWE", "Sweden", "UEFA", 3, False, 1790),
    TeamSeed("TUN", "Tunisia", "CAF", 4, False, 1700),
    TeamSeed("BEL", "Belgium", "UEFA", 1, False, 1900),
    TeamSeed("EGY", "Egypt", "CAF", 3, False, 1730),
    TeamSeed("IRN", "IR Iran", "AFC", 2, False, 1780),
    TeamSeed("NZL", "New Zealand", "OFC", 4, False, 1580),
    TeamSeed("ESP", "Spain", "UEFA", 1, False, 2050),
    TeamSeed("CPV", "Cabo Verde", "CAF", 4, False, 1600),
    TeamSeed("KSA", "Saudi Arabia", "AFC", 3, False, 1690),
    TeamSeed("URU", "Uruguay", "CONMEBOL", 2, False, 1860),
    TeamSeed("FRA", "France", "UEFA", 1, False, 2060),
    TeamSeed("SEN", "Senegal", "CAF", 2, False, 1800),
    TeamSeed("NOR", "Norway", "UEFA", 3, False, 1760),
    TeamSeed("IRQ", "Iraq", "AFC", 4, False, 1620),
    TeamSeed("ARG", "Argentina", "CONMEBOL", 1, False, 2080),
    TeamSeed("ALG", "Algeria", "CAF", 3, False, 1720),
    TeamSeed("AUT", "Austria", "UEFA", 3, False, 1790),
    TeamSeed("JOR", "Jordan", "AFC", 4, False, 1580),
    TeamSeed("POR", "Portugal", "UEFA", 1, False, 1990),
    TeamSeed("COD", "Congo DR", "CAF", 4, False, 1620),
    TeamSeed("UZB", "Uzbekistan", "AFC", 4, False, 1640),
    TeamSeed("COL", "Colombia", "CONMEBOL", 2, False, 1850),
    TeamSeed("ENG", "England", "UEFA", 1, False, 2010),
    TeamSeed("CRO", "Croatia", "UEFA", 2, False, 1890),
    TeamSeed("GHA", "Ghana", "CAF", 4, False, 1700),
    TeamSeed("PAN", "Panama", "CONCACAF", 4, False, 1640),
]


STAGE_MAP = {
    "R32": "r32",
    "R16": "r16",
    "QF": "qf",
    "SF": "sf",
    "3rd": "third",
    "Final": "final",
}


def fetch_raw(title: str) -> str:
    response = requests.get(WIKI_RAW.format(title=title), headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def clean_wiki(value: str) -> str:
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    value = re.sub(r"<ref.*?</ref>", "", value, flags=re.S)
    value = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    value = value.replace("&nbsp;", " ")
    return " ".join(value.strip().split())


def parse_team(value: str) -> str:
    match = re.search(r"\|([A-Z]{3})\}\}", value)
    if match:
        return match.group(1)
    return clean_wiki(value)


def parse_date(value: str) -> str:
    match = re.search(r"Start date\|(\d{4})\|0?(\d{1,2})\|0?(\d{1,2})", value)
    if not match:
        raise ValueError(f"could not parse date: {value}")
    year, month, day = map(int, match.groups())
    return dt.date(year, month, day).isoformat()


def parse_time(value: str) -> str:
    value = value.replace("&nbsp;", " ")
    match = re.search(r"(\d{1,2}):(\d{2})\s*([ap])\.m\.", value, flags=re.I)
    if not match:
        return clean_wiki(value)
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3).lower()
    if meridiem == "p" and hour != 12:
        hour += 12
    if meridiem == "a" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if not line.startswith("|") or "=" not in line:
            continue
        key, value = line[1:].split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def iter_sections(raw: str, section_re: str) -> Iterable[tuple[str, str]]:
    for match in re.finditer(section_re, raw):
        section = match.group(1)
        end_marker = f"<section end={section}"
        end = raw.find(end_marker, match.end())
        if end == -1:
            continue
        yield section, raw[match.end():end]


def match_number(score: str) -> int:
    matches = re.findall(r"Match\s+(\d+)", score)
    if not matches:
        raise ValueError(f"could not parse match number: {score}")
    return int(matches[-1])


def fixture_from_block(section: str, block: str, group: str | None, stage: str) -> dict[str, object]:
    fields = parse_fields(block)
    number = match_number(fields["score"])
    return {
        "match_id": f"M{number:03d}",
        "date": parse_date(fields["date"]),
        "kickoff": parse_time(fields.get("time", "")),
        "stage": stage,
        "group": group,
        "venue": clean_wiki(fields.get("stadium", "")),
        "home": parse_team(fields["team1"]),
        "away": parse_team(fields["team2"]),
        "neutral": True,
    }


def load_fixtures() -> list[dict[str, object]]:
    fixtures: list[dict[str, object]] = []
    for group in "ABCDEFGHIJKL":
        raw = fetch_raw(f"2026_FIFA_World_Cup_Group_{group}")
        for section, block in iter_sections(raw, rf"<section begin=({group}\d+) />"):
            fixtures.append(fixture_from_block(section, block, group, "group"))

    knockout_raw = fetch_raw("2026_FIFA_World_Cup_knockout_stage")
    for section, block in iter_sections(knockout_raw, r"<section begin=([A-Za-z0-9-]+) />"):
        if section.startswith("R32"):
            prefix = "R32"
        elif section.startswith("R16"):
            prefix = "R16"
        elif section == "3rd":
            prefix = "3rd"
        else:
            prefix = re.sub(r"\d+$", "", section)
        stage = STAGE_MAP.get(prefix)
        if not stage:
            continue
        fixtures.append(fixture_from_block(section, block, None, stage))

    final_raw = fetch_raw("2026_FIFA_World_Cup_final")
    final_match = re.search(r"<section begin=\"Final\" />(.*?)<section end=\"Final\" />", final_raw, re.S)
    if final_match:
        fixtures.append(fixture_from_block("Final", final_match.group(1), None, "final"))

    return sorted(fixtures, key=lambda f: int(str(f["match_id"])[1:]))


def write_teams() -> None:
    rows = [["code", "name", "confederation", "pot", "is_host", "elo_seed"]]
    for team in TEAMS:
        rows.append([
            team.code,
            team.name,
            team.confederation,
            team.pot,
            int(team.is_host),
            team.elo_seed,
        ])
    with TEAMS_CSV.open("w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerows(rows)
    TEAMS_JSON.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "code": t.code,
                        "name": t.name,
                        "confederation": t.confederation,
                        "pot": t.pot,
                        "is_host": t.is_host,
                        "elo_seed": t.elo_seed,
                    }
                    for t in TEAMS
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def write_fixtures(fixtures: list[dict[str, object]]) -> None:
    rows = [["match_id", "date", "kickoff", "stage", "group", "venue", "home", "away", "neutral"]]
    for fixture in fixtures:
        rows.append([
            fixture["match_id"],
            fixture["date"],
            fixture["kickoff"],
            fixture["stage"],
            fixture["group"] or "",
            fixture["venue"],
            fixture["home"],
            fixture["away"],
            int(bool(fixture["neutral"])),
        ])
    with FIXTURES_CSV.open("w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerows(rows)
    FIXTURES_JSON.write_text(json.dumps({"items": fixtures}, indent=2), encoding="utf-8")


def update_status() -> None:
    now = dt.datetime.utcnow().isoformat() + "Z"
    try:
        current = json.loads(DATA_STATUS_JSON.read_text(encoding="utf-8"))
    except Exception:
        current = {}
    current.update(
        {
            "fixtures_source": "FIFA_OFFICIAL",
            "is_sample": current.get("results_source") == "SAMPLE",
            "fixtures_note": (
                "FIFA World Cup 2026 official match schedule, including all 104 matches. "
                f"Source: {OFFICIAL_SOURCE_URL}"
            ),
            "generated_at": now,
        }
    )
    DATA_STATUS_JSON.write_text(json.dumps(current, indent=2), encoding="utf-8")


def main() -> int:
    ensure_dirs()
    fixtures = load_fixtures()
    if len(fixtures) != 104:
        print(f"[sync_wc26_schedule] expected 104 fixtures, got {len(fixtures)}", file=sys.stderr)
        return 1
    write_teams()
    write_fixtures(fixtures)
    update_status()
    print(f"[sync_wc26_schedule] wrote {len(TEAMS)} teams -> {TEAMS_CSV}")
    print(f"[sync_wc26_schedule] wrote {len(fixtures)} fixtures -> {FIXTURES_CSV}")
    print(f"[sync_wc26_schedule] source: {OFFICIAL_SOURCE_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
