"""Confirm the bundled official WC26 teams + fixtures are present."""
from __future__ import annotations
import json
import sys
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wc_predict.paths import DATA_STATUS_JSON, FIXTURES_CSV, TEAMS_CSV, ensure_dirs  # noqa: E402

OFFICIAL_SOURCE_URL = (
    "https://www.fifa.com/en/tournaments/mens/worldcup/"
    "canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums"
)


def update_status() -> None:
    try:
        status = json.loads(DATA_STATUS_JSON.read_text(encoding="utf-8"))
    except Exception:
        status = {}
    status.update(
        {
            "fixtures_source": "FIFA_OFFICIAL",
            "is_sample": status.get("results_source") == "SAMPLE",
            "fixtures_note": (
                "FIFA World Cup 2026 official match schedule, including all 104 matches. "
                f"Source: {OFFICIAL_SOURCE_URL}"
            ),
            "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        }
    )
    DATA_STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    DATA_STATUS_JSON.write_text(json.dumps(status, indent=2), encoding="utf-8")


def main() -> int:
    ensure_dirs()
    try:
        import sync_wc26_schedule

        rc = sync_wc26_schedule.main()
        if rc == 0:
            return 0
        print("[fetch_fixtures] Live schedule sync failed; checking bundled files.", file=sys.stderr)
    except Exception as exc:
        print(f"[fetch_fixtures] Live schedule sync failed: {exc}", file=sys.stderr)
        print("[fetch_fixtures] Falling back to bundled official schedule files.", file=sys.stderr)

    missing = [str(path) for path in (TEAMS_CSV, FIXTURES_CSV) if not path.exists()]
    if missing:
        print("[fetch_fixtures] Missing bundled official schedule files:", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        print("[fetch_fixtures] Run python ml/scripts/sync_wc26_schedule.py to regenerate them.", file=sys.stderr)
        return 1
    update_status()
    print(f"[fetch_fixtures] Using bundled official FIFA WC26 teams: {TEAMS_CSV}")
    print(f"[fetch_fixtures] Using bundled official FIFA WC26 fixtures: {FIXTURES_CSV}")
    print(f"[fetch_fixtures] Source: {OFFICIAL_SOURCE_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
