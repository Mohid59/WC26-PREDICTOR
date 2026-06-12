"""Fetch official 2026 FIFA World Cup squads from Wikipedia into public/data/squads.json.

Usage: python ml/fetch_squads.py
Re-run any time squads change (injury replacements); commit the regenerated JSON.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

WIKI_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "data" / "squads.json"
TEAMS = ROOT / "public" / "data" / "teams.json"

POS_MAP = {"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW"}


def team_name_to_code() -> dict[str, str]:
    items = json.loads(TEAMS.read_text(encoding="utf-8"))["items"]
    m = {t["name"].lower(): t["code"] for t in items}
    # Wikipedia naming differences vs teams.json
    aliases = {
        "south korea": "KOR",
        "korea republic": "KOR",
        "united states": "USA",
        "ivory coast": "CIV",
        "cote d'ivoire": "CIV",
        "côte d'ivoire": "CIV",
        "bosnia and herzegovina": "BIH",
        "czech republic": "CZE",
        "czechia": "CZE",
        "turkey": "TUR",
        "türkiye": "TUR",
        "dr congo": "COD",
        "democratic republic of the congo": "COD",
        "cape verde": "CPV",
        "cabo verde": "CPV",
        "iran": "IRN",
        "curacao": "CUW",
        "curaçao": "CUW",
        "new zealand": "NZL",
        "saudi arabia": "KSA",
    }
    for k, v in aliases.items():
        m.setdefault(k, v)
    return m


def parse_int(text: str) -> int | None:
    t = re.sub(r"\D", "", text or "")
    return int(t) if t else None


def parse_age(text: str) -> int | None:
    m = re.search(r"aged?\s*(\d+)", text or "", re.I)
    if m:
        return int(m.group(1))
    return parse_int(text)


def main() -> int:
    name_to_code = team_name_to_code()
    html = requests.get(
        WIKI_URL, headers={"User-Agent": "WC26-Predictor/1.0 (squad data sync)"}, timeout=60
    ).text
    soup = BeautifulSoup(html, "lxml")

    squads: dict[str, dict] = {}
    # Each team is an h3 heading followed by a coach line and a squad wikitable.
    for heading in soup.select("h3"):
        team_name = heading.get_text(" ", strip=True)
        team_name = re.sub(r"\[.*?\]", "", team_name).strip()
        code = name_to_code.get(team_name.lower())
        if not code:
            continue

        # Walk forward to the next squad table before the next h3.
        node = heading
        coach = None
        table = None
        # headings are wrapped in div.mw-heading on current wiki markup
        start = heading.parent if heading.parent and "mw-heading" in (heading.parent.get("class") or []) else heading
        for sib in start.find_all_next():
            if sib.name == "h3" and sib is not heading:
                break
            if sib.name == "p" and coach is None:
                txt = sib.get_text(" ", strip=True)
                m = re.search(r"head coach:?\s*(.+)$", txt, re.I) or re.search(
                    r"coach:?\s*(.+)$", txt, re.I
                )
                if m:
                    coach = re.sub(r"\[.*?\]", "", m.group(1)).strip()
            if sib.name == "table" and "wikitable" in (sib.get("class") or []):
                table = sib
                break
        if table is None:
            continue

        players = []
        for tr in table.select("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 7:
                continue
            texts = [c.get_text(" ", strip=True) for c in cells]
            number = parse_int(texts[0])
            pos = re.sub(r"\d", "", texts[1]).strip().upper()
            pos = POS_MAP.get(pos, pos)
            if pos not in POS_MAP:
                continue
            name = re.sub(r"\s*\(.*?\)\s*", " ", texts[2]).strip()
            name = re.sub(r"\[.*?\]", "", name).strip()
            if not name:
                continue
            age = parse_age(texts[3])
            caps = parse_int(texts[4])
            goals = parse_int(texts[5])
            club_cell = cells[6]
            club = club_cell.get_text(" ", strip=True)
            club = re.sub(r"\[.*?\]", "", club).strip() or None
            players.append(
                {
                    "number": number,
                    "name": name,
                    "position": pos,
                    "age": age,
                    "caps": caps,
                    "goals": goals,
                    "club": club,
                }
            )

        if players:
            squads[code] = {"team": code, "coach": coach, "players": players}

    print(f"parsed {len(squads)} squads")
    missing = set(name_to_code.values()) - set(squads)
    if missing:
        print("missing:", sorted(missing), file=sys.stderr)

    OUT.write_text(
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "source": WIKI_URL,
                "squads": squads,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    return 0 if len(squads) >= 40 else 1


if __name__ == "__main__":
    raise SystemExit(main())
