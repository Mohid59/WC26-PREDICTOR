"""Bundled sample data: 48 WC26 qualifiers (projected) + group draw + historical seed.

This module produces clearly-labelled SAMPLE data so the pipeline can run end-to-end
without external network calls. Production deployments should replace this with
authoritative FIFA sources via ``ml/scripts/fetch_*``.

The 48-team list is a plausible projected roster of WC26 qualifiers based on FIFA
ranking trajectory and historical participation patterns. It is NOT an official
qualification list. The UI surfaces a "sample data" badge whenever this seed is in use.
"""
from __future__ import annotations
import csv
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SeedTeam:
    code: str
    name: str
    confederation: str
    pot: int  # FIFA pot 1..4 (based on ranking)
    is_host: bool = False


# 48 plausible WC26 qualifiers. Hosts in pot 1 per FIFA convention.
SEED_TEAMS: list[SeedTeam] = [
    # Pot 1 — hosts + top ranked
    SeedTeam("USA", "United States", "CONCACAF", 1, True),
    SeedTeam("MEX", "Mexico", "CONCACAF", 1, True),
    SeedTeam("CAN", "Canada", "CONCACAF", 1, True),
    SeedTeam("ARG", "Argentina", "CONMEBOL", 1),
    SeedTeam("FRA", "France", "UEFA", 1),
    SeedTeam("ESP", "Spain", "UEFA", 1),
    SeedTeam("ENG", "England", "UEFA", 1),
    SeedTeam("BRA", "Brazil", "CONMEBOL", 1),
    SeedTeam("POR", "Portugal", "UEFA", 1),
    SeedTeam("NED", "Netherlands", "UEFA", 1),
    SeedTeam("BEL", "Belgium", "UEFA", 1),
    SeedTeam("GER", "Germany", "UEFA", 1),
    # Pot 2
    SeedTeam("CRO", "Croatia", "UEFA", 2),
    SeedTeam("ITA", "Italy", "UEFA", 2),
    SeedTeam("MAR", "Morocco", "CAF", 2),
    SeedTeam("COL", "Colombia", "CONMEBOL", 2),
    SeedTeam("URU", "Uruguay", "CONMEBOL", 2),
    SeedTeam("JPN", "Japan", "AFC", 2),
    SeedTeam("SUI", "Switzerland", "UEFA", 2),
    SeedTeam("SEN", "Senegal", "CAF", 2),
    SeedTeam("IRN", "Iran", "AFC", 2),
    SeedTeam("KOR", "South Korea", "AFC", 2),
    SeedTeam("DEN", "Denmark", "UEFA", 2),
    SeedTeam("AUS", "Australia", "AFC", 2),
    # Pot 3
    SeedTeam("AUT", "Austria", "UEFA", 3),
    SeedTeam("POL", "Poland", "UEFA", 3),
    SeedTeam("UKR", "Ukraine", "UEFA", 3),
    SeedTeam("TUR", "Turkey", "UEFA", 3),
    SeedTeam("NOR", "Norway", "UEFA", 3),
    SeedTeam("EGY", "Egypt", "CAF", 3),
    SeedTeam("ALG", "Algeria", "CAF", 3),
    SeedTeam("NGA", "Nigeria", "CAF", 3),
    SeedTeam("ECU", "Ecuador", "CONMEBOL", 3),
    SeedTeam("PAR", "Paraguay", "CONMEBOL", 3),
    SeedTeam("SAU", "Saudi Arabia", "AFC", 3),
    SeedTeam("QAT", "Qatar", "AFC", 3),
    # Pot 4
    SeedTeam("IRQ", "Iraq", "AFC", 4),
    SeedTeam("UZB", "Uzbekistan", "AFC", 4),
    SeedTeam("CIV", "Ivory Coast", "CAF", 4),
    SeedTeam("CMR", "Cameroon", "CAF", 4),
    SeedTeam("GHA", "Ghana", "CAF", 4),
    SeedTeam("TUN", "Tunisia", "CAF", 4),
    SeedTeam("CRC", "Costa Rica", "CONCACAF", 4),
    SeedTeam("PAN", "Panama", "CONCACAF", 4),
    SeedTeam("JAM", "Jamaica", "CONCACAF", 4),
    SeedTeam("NZL", "New Zealand", "OFC", 4),
    SeedTeam("BOL", "Bolivia", "CONMEBOL", 4),
    SeedTeam("COD", "DR Congo", "CAF", 4),
]

# Plausible baseline Elo per team (used to seed history + to simulate when no
# real history exists). Top teams ~2000, mid ~1700, low ~1500.
BASELINE_ELO: dict[str, float] = {
    "ARG": 2080, "FRA": 2060, "ESP": 2050, "ENG": 2010, "BRA": 2030, "POR": 1990,
    "NED": 1960, "BEL": 1900, "GER": 1940, "CRO": 1890, "ITA": 1900, "COL": 1850,
    "URU": 1860, "MAR": 1830, "JPN": 1820, "USA": 1810, "MEX": 1810, "CAN": 1740,
    "SUI": 1820, "SEN": 1800, "IRN": 1780, "KOR": 1780, "DEN": 1830, "AUS": 1770,
    "AUT": 1790, "POL": 1750, "UKR": 1740, "TUR": 1770, "NOR": 1760, "EGY": 1730,
    "ALG": 1720, "NGA": 1730, "ECU": 1740, "PAR": 1700, "SAU": 1690, "QAT": 1700,
    "IRQ": 1620, "UZB": 1640, "CIV": 1710, "CMR": 1720, "GHA": 1700, "TUN": 1700,
    "CRC": 1660, "PAN": 1640, "JAM": 1610, "NZL": 1580, "BOL": 1600, "COD": 1620,
}


def assign_groups(seed: int = 42) -> dict[str, list[str]]:
    """Snake-draw groups A..L respecting pot + confederation constraints.

    Real FIFA draw applies geographic constraints (max 1 UEFA in pot 1 hosts groups,
    max 1 from same confederation per group except UEFA which allows 2). We
    approximate that for sample data; the UI labels these as sample groups.
    """
    rng = random.Random(seed)
    pots = {p: [t.code for t in SEED_TEAMS if t.pot == p] for p in (1, 2, 3, 4)}
    for p in pots:
        rng.shuffle(pots[p])
    groups = {chr(ord("A") + i): [] for i in range(12)}
    group_keys = list(groups.keys())
    # Place hosts in A, B, C (USA, MEX, CAN) — FIFA convention
    hosts_first = {"USA": "A", "MEX": "B", "CAN": "C"}
    for code, g in hosts_first.items():
        groups[g].append(code)
        pots[1].remove(code)
    # Fill pot 1 remaining in D..L
    for code in pots[1]:
        for g in group_keys[3:]:
            if not groups[g]:
                groups[g].append(code)
                break

    # Pots 2-4: respect confederation constraints best-effort
    code_to_team = {t.code: t for t in SEED_TEAMS}
    for pot_idx in (2, 3, 4):
        order = group_keys[:]
        if pot_idx % 2 == 0:
            order = order[::-1]
        idx = 0
        remaining = pots[pot_idx][:]
        for g in order:
            placed = False
            for cand in remaining:
                confs_in_group = {code_to_team[c].confederation for c in groups[g]}
                ccand = code_to_team[cand].confederation
                # UEFA allows up to 2 per group; others max 1
                if ccand == "UEFA":
                    uefa_count = sum(1 for c in groups[g] if code_to_team[c].confederation == "UEFA")
                    if uefa_count >= 2:
                        continue
                else:
                    if ccand in confs_in_group:
                        continue
                groups[g].append(cand)
                remaining.remove(cand)
                placed = True
                break
            if not placed and remaining:
                groups[g].append(remaining.pop(0))
            idx += 1
        # any left over (constraint conflict) — pack into first groups missing a slot
        for cand in remaining:
            for g in group_keys:
                if len(groups[g]) < pot_idx:
                    groups[g].append(cand)
                    break
    return groups


VENUES = [
    "Estadio Azteca, Mexico City", "MetLife Stadium, East Rutherford",
    "SoFi Stadium, Inglewood", "AT&T Stadium, Arlington", "Levi's Stadium, Santa Clara",
    "Mercedes-Benz Stadium, Atlanta", "Lincoln Financial Field, Philadelphia",
    "Hard Rock Stadium, Miami Gardens", "NRG Stadium, Houston",
    "Arrowhead Stadium, Kansas City", "Gillette Stadium, Foxborough",
    "Lumen Field, Seattle", "BMO Field, Toronto", "BC Place, Vancouver",
    "Estadio Akron, Guadalajara", "Estadio BBVA, Monterrey",
]


def write_teams_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "name", "confederation", "pot", "is_host", "elo_seed"])
        for t in SEED_TEAMS:
            w.writerow([t.code, t.name, t.confederation, t.pot, int(t.is_host), BASELINE_ELO.get(t.code, 1600)])


def write_fixtures_csv(path: Path, groups: dict[str, list[str]]) -> None:
    """Generate group-stage fixtures (12 groups × 6 matches = 72).

    Start date 2026-06-11 (tournament opening). Each group plays 3 matchdays
    spaced roughly 4 days apart.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)
    base = date(2026, 6, 11)
    rows = [["match_id", "date", "kickoff", "stage", "group", "venue", "home", "away", "neutral"]]
    match_no = 1
    matchday_offsets = [0, 4, 8]
    for g_idx, (g, teams) in enumerate(groups.items()):
        if len(teams) < 4:
            continue
        t1, t2, t3, t4 = teams[:4]
        pairs = [
            (t1, t2), (t3, t4),  # MD1
            (t1, t3), (t2, t4),  # MD2
            (t1, t4), (t2, t3),  # MD3
        ]
        for md, (home, away) in enumerate(pairs):
            d = base + timedelta(days=matchday_offsets[md // 2] + (g_idx % 3))
            kickoff = ["12:00", "15:00", "18:00", "21:00"][match_no % 4]
            venue = VENUES[rng.randrange(len(VENUES))]
            rows.append([
                f"G{match_no:03d}", d.isoformat(), kickoff, "group", g, venue, home, away, 1,
            ])
            match_no += 1
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def write_history_csv(path: Path, seed: int = 42, n: int = 1200) -> None:
    """Generate a deterministic synthetic historical results CSV.

    This is CLEARLY SAMPLE data. Outcomes are drawn from an Elo-derived Poisson
    model around the baseline ratings, then nudged slightly so the trained model
    has signal to learn rather than memorising fixed labels. Honestly labelled as
    synthetic so the UI badges this state.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    import math
    teams = [t.code for t in SEED_TEAMS]
    base = date(2022, 1, 1)
    end = date(2026, 5, 1)
    total_days = (end - base).days
    rows = [["date", "home", "away", "home_goals", "away_goals", "tournament", "neutral"]]
    for _ in range(n):
        d = base + timedelta(days=rng.randrange(total_days))
        a, b = rng.sample(teams, 2)
        ra = BASELINE_ELO.get(a, 1600)
        rb = BASELINE_ELO.get(b, 1600)
        neutral = rng.random() < 0.45
        home_adv = 0 if neutral else 60.0
        diff = (ra + home_adv - rb) / 400.0
        # Expected goals: simple log-linear around 1.4 average per side
        lam_a = max(0.15, 1.45 * math.exp(0.35 * diff) + rng.gauss(0, 0.2))
        lam_b = max(0.15, 1.45 * math.exp(-0.35 * diff) + rng.gauss(0, 0.2))
        # Poisson via inverse-method approximation
        def poisson(lam: float) -> int:
            L = math.exp(-lam); k = 0; p = 1.0
            while True:
                k += 1
                p *= rng.random()
                if p <= L:
                    return k - 1
        ga = poisson(lam_a); gb = poisson(lam_b)
        tourn = rng.choice(["friendly", "qualifier", "qualifier", "friendly", "uefa_nations", "copa_america"])
        rows.append([d.isoformat(), a, b, ga, gb, tourn, int(neutral)])
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)


def write_all(raw_dir: Path, seed: int = 42, write_history: bool = False) -> dict[str, str]:
    """Write teams + fixtures. Only overwrites results.csv if write_history=True.

    fetch_fixtures.py calls this with write_history=False to preserve whatever
    fetch_results.py produced (real or sample).
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    teams_path = raw_dir / "teams_wc2026.csv"
    fixtures_path = raw_dir / "fixtures_wc2026.csv"
    write_teams_csv(teams_path)
    groups = assign_groups(seed=seed)
    write_fixtures_csv(fixtures_path, groups)
    out = {
        "teams": str(teams_path),
        "fixtures": str(fixtures_path),
        "groups": ",".join(f"{g}:{'-'.join(t)}" for g, t in groups.items()),
    }
    if write_history:
        results_path = raw_dir / "results.csv"
        write_history_csv(results_path, seed=seed)
        out["results"] = str(results_path)
    return out
