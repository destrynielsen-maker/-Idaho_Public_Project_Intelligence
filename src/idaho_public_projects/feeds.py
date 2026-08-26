from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator


def _dt(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _active(row: dict) -> bool:
    return row.get("stage") not in {"CLOSED", "BID_RESULTS", "AWARDED"} and row.get("status") not in {"CLOSED", "RESULTS", "COMPLETED"}


def _treasure(row: dict) -> bool:
    text = f"{row.get('location','')} {row.get('title','')} {row.get('description','')}".lower()
    return any(x in text for x in ("boise", "meridian", "nampa", "caldwell", "eagle", "kuna", "star", "garden city", "ada county"))


def _feed(rows: list[dict], title: str, path: Path, site_base: str):
    fg = FeedGenerator()
    fg.id(site_base)
    fg.title(title)
    fg.link(href=site_base, rel="alternate")
    fg.description(f"{title} — Idaho Public Project Intelligence")
    fg.language("en")
    for row in sorted(rows, key=lambda r: (r.get("score", 0), r.get("due_date", "")), reverse=True)[:150]:
        entry = fg.add_entry()
        entry.id(row.get("id") or row.get("url") or row.get("title"))
        entry.title(f"[{row.get('score',0)}] {row.get('title','')}")
        entry.link(href=row.get("url") or site_base)
        entry.description(
            f"Agency: {row.get('agency','')} | Stage: {row.get('stage','')} | "
            f"Type: {row.get('solicitation_type','')} | Due: {row.get('due_date','') or 'TBD'} | "
            f"Location: {row.get('location','')}<br>{row.get('description','')[:1200]}"
        )
        when = _dt(row.get("posted_date") or row.get("first_seen") or "")
        if when:
            entry.published(when)
    path.parent.mkdir(parents=True, exist_ok=True)
    fg.rss_file(str(path), pretty=True)


def write_all(rows: list[dict], out_dir: Path, site_base: str):
    today = date.today()
    week_ago = today - timedelta(days=7)
    two_weeks = today + timedelta(days=14)
    feeds = {
        "all-public-projects.xml": ("All Idaho Public Opportunities", [r for r in rows if _active(r)]),
        "treasure-valley.xml": ("Treasure Valley Public Opportunities", [r for r in rows if _active(r) and _treasure(r)]),
        "construction.xml": ("Construction Opportunities", [r for r in rows if _active(r) and r.get("category") in {"BUILDING", "CIVIL"}]),
        "building-projects.xml": ("Building & Facility Projects", [r for r in rows if _active(r) and r.get("category") == "BUILDING"]),
        "materials-equipment.xml": ("Materials & Equipment Opportunities", [r for r in rows if _active(r) and r.get("category") == "MATERIALS_EQUIPMENT"]),
        "design-rfq.xml": ("Design / RFQ / Preconstruction", [r for r in rows if _active(r) and (r.get("solicitation_type") in {"RFQ", "RFP"} or r.get("stage") in {"FUTURE", "UPCOMING", "DESIGN_RFQ", "DESIGN_RFP"})]),
        "awards.xml": ("Bid Results & Awards", [r for r in rows if r.get("stage") in {"BID_RESULTS", "AWARDED"}]),
        "early-opportunities.xml": ("Early & Future Opportunities", [r for r in rows if r.get("source") == "Idaho Purchasing" or r.get("stage") in {"FUTURE", "UPCOMING"}]),
    }

    closing, new = [], []
    for r in rows:
        due = _dt(r.get("due_date", ""))
        if _active(r) and due and today <= due.date() <= two_weeks:
            closing.append(r)
        seen = _dt(r.get("first_seen", ""))
        if seen and seen.date() >= week_ago:
            new.append(r)
    feeds["closing-14-days.xml"] = ("Closing in the Next 14 Days", closing)
    feeds["new-this-week.xml"] = ("New This Week", new)

    for filename, (title, selected) in feeds.items():
        _feed(selected, title, out_dir / filename, site_base)
