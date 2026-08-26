from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from ..models import Opportunity
from ..utils import USER_AGENT, clean, http_get, parse_date, stable_id

URL = "https://purchasing.idaho.gov/open-and-future-solicitations/"
REPORT_URL = "https://purchasing.idaho.gov/wp-json/wm4/v1/procurement-report"


def _date(value: str) -> str:
    """Normalize the report's date-only or ISO timestamp fields."""
    raw = clean(value)
    if "T" in raw:
        raw = raw.split("T", 1)[0]
    return parse_date(raw)


def _solicitation_parts(name: str) -> tuple[str, str]:
    match = re.search(r"\b(RFI|RFQ|RFP|ITB)\s*[-#:]?\s*([A-Za-z0-9-]+)", name or "", re.I)
    if not match:
        return "FUTURE_SOLICITATION", ""
    kind = match.group(1).upper()
    number = f"{kind} {match.group(2)}"
    return kind, number


def _stage(start: str, completed: str, status: str) -> str:
    if completed or (status or "").strip().lower() == "completed":
        return "AWARDED"
    return "UPCOMING" if start else "FUTURE"


def parse_report(payload: dict) -> list[Opportunity]:
    data = payload.get("data", []) if isinstance(payload, dict) else []
    if not isinstance(data, list):
        return []

    results: list[Opportunity] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = clean(str(item.get("name") or ""))
        agency = clean(str(item.get("agency") or ""))
        if not name or not agency:
            continue

        description = clean(str(item.get("project_description") or ""))
        created = _date(str(item.get("project_created_date") or ""))
        start = _date(str(item.get("project_start_date") or ""))
        due = _date(str(item.get("project_due_date") or ""))
        updated = _date(str(item.get("latest_update_date") or ""))
        completed = _date(str(item.get("project_completed_date") or ""))
        status = clean(str(item.get("status") or ""))
        solicitation_type, solicitation_number = _solicitation_parts(name)

        results.append(
            Opportunity(
                id=stable_id(
                    "idaho-purchasing",
                    solicitation_number,
                    f"{agency}|{name}",
                ),
                source="Idaho Purchasing",
                title=name,
                agency=agency,
                description=description,
                location="Idaho",
                stage=_stage(start, completed, status),
                solicitation_type=solicitation_type,
                solicitation_number=solicitation_number,
                posted_date=created,
                open_date=start,
                due_date=due,
                updated_date=updated,
                status=status.upper() if status else "PLANNED",
                url=URL,
            )
        )
    return results


def parse_html(html: str) -> list[Opportunity]:
    """Fallback for a future server-rendered version of the official table."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[Opportunity] = []
    for table in soup.find_all("table"):
        headers = [clean(x.get_text(" ", strip=True)).lower() for x in table.find_all("th")]
        if headers and "agency" not in headers:
            continue
        for row in table.find_all("tr"):
            cells = [clean(c.get_text(" ", strip=True)) for c in row.find_all(["td", "th"])]
            if len(cells) < 6 or cells[0].lower() in {"name", ""}:
                continue
            cells += [""] * (9 - len(cells))
            name, agency, overview, created, start, due, updated, completed, status = cells[:9]
            if not name or not agency:
                continue
            solicitation_type, solicitation_number = _solicitation_parts(name)
            results.append(
                Opportunity(
                    id=stable_id("idaho-purchasing", solicitation_number, f"{agency}|{name}"),
                    source="Idaho Purchasing",
                    title=name,
                    agency=agency,
                    description=overview,
                    location="Idaho",
                    stage=_stage(parse_date(start), parse_date(completed), status),
                    solicitation_type=solicitation_type,
                    solicitation_number=solicitation_number,
                    posted_date=parse_date(created),
                    open_date=parse_date(start),
                    due_date=parse_date(due),
                    updated_date=parse_date(updated),
                    status=status.upper() if status else ("COMPLETED" if completed else "PLANNED"),
                    url=URL,
                )
            )
    return results


def collect() -> list[Opportunity]:
    try:
        response = requests.get(
            REPORT_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=35,
        )
        response.raise_for_status()
        rows = parse_report(response.json())
        if rows:
            return rows
    except (requests.RequestException, ValueError):
        pass
    return parse_html(http_get(URL))
