from __future__ import annotations

import json

import requests
from bs4 import BeautifulSoup

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, stable_id, USER_AGENT

URL = "https://purchasing.idaho.gov/open-and-future-solicitations/"
REPORT_URL = "https://purchasing.idaho.gov/wp-json/wm4/v1/procurement-report"


def parse_html(html: str) -> list[Opportunity]:
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
            stage = "FUTURE"
            if completed or status.lower() == "completed":
                stage = "AWARDED"
            elif start:
                stage = "UPCOMING"
            results.append(
                Opportunity(
                    id=stable_id("idaho-purchasing", "", f"{agency}|{name}"),
                    source="Idaho Purchasing",
                    title=name,
                    agency=agency,
                    description=overview,
                    location="Idaho",
                    stage=stage,
                    solicitation_type="FUTURE_SOLICITATION",
                    posted_date=parse_date(created),
                    open_date=parse_date(start),
                    due_date=parse_date(due),
                    updated_date=parse_date(updated),
                    status=status or ("COMPLETED" if completed else "PLANNED"),
                    url=URL,
                )
            )
    return results


def _report_payload() -> dict:
    response = requests.get(
        REPORT_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=35,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Idaho Purchasing report payload is not an object")
    return payload


def collect() -> list[Opportunity]:
    payload = _report_payload()
    data = payload.get("data", [])
    print(f"IDAHO_PURCHASING_DIAG endpoint_count={len(data) if isinstance(data, list) else 'non-list'}")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            print("IDAHO_PURCHASING_DIAG endpoint_keys=" + ",".join(sorted(first.keys())))
            safe_preview = {k: first.get(k) for k in sorted(first.keys())}
            print("IDAHO_PURCHASING_DIAG endpoint_first=" + json.dumps(safe_preview, ensure_ascii=True)[:5000])
    return []
