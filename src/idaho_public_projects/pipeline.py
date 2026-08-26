from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .classify import classify
from .collectors import achd, boise, dpw, purchasing
from .models import Opportunity


COLLECTORS = [
    ("City of Boise", boise.collect),
    ("Idaho DPW", dpw.collect),
    ("Idaho Purchasing", purchasing.collect),
    ("ACHD", achd.collect),
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_history(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {row["id"]: row for row in payload.get("opportunities", []) if row.get("id")}
    except Exception:
        return {}


def run(data_path: Path = Path("data/opportunities.json")) -> tuple[dict, dict]:
    now = _now()
    history = _load_history(data_path)
    current: dict[str, Opportunity] = {}
    statuses: list[dict] = []

    for source, collector in COLLECTORS:
        try:
            rows = collector()
            for row in rows:
                classify(row)
                old = history.get(row.id, {})
                row.first_seen = old.get("first_seen") or now
                row.last_seen = now
                current[row.id] = row
            statuses.append({
                "source": source,
                "status": "OK" if rows else "EMPTY",
                "records_seen": len(rows),
                "qualifying_records": len(rows),
                "note": "" if rows else "No records parsed from public source; collector may need source-specific refinement.",
            })
        except Exception as exc:
            statuses.append({
                "source": source,
                "status": "ERROR",
                "records_seen": 0,
                "qualifying_records": 0,
                "note": f"{type(exc).__name__}: {exc}",
            })

    merged: dict[str, dict] = dict(history)
    for oid, row in current.items():
        merged[oid] = row.to_dict()

    opportunities = sorted(
        merged.values(),
        key=lambda r: (r.get("score", 0), r.get("due_date", ""), r.get("posted_date", "")),
        reverse=True,
    )
    return (
        {"generated_at": now, "opportunities": opportunities},
        {"generated_at": now, "collector_status": statuses},
    )
