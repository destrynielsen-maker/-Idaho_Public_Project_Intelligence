from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, stable_id

URL = "https://purchasing.idaho.gov/open-and-future-solicitations/"


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


def _diagnose_dynamic_source(html: str) -> None:
    """Temporary branch-only diagnostic for the dynamic State Purchasing table."""
    soup = BeautifulSoup(html, "html.parser")
    scripts = []
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            scripts.append(urljoin(URL, src))
    print("IDAHO_PURCHASING_DIAG script_srcs:")
    for src in scripts:
        print(f"IDAHO_PURCHASING_DIAG SCRIPT {src}")

    text = html.replace("\n", " ")
    patterns = ["asana", "admin-ajax", "wp-json", "solicitation", "future", "datatable", "dataTable"]
    for pattern in patterns:
        for match in list(re.finditer(pattern, text, re.I))[:4]:
            start = max(0, match.start() - 220)
            end = min(len(text), match.end() + 420)
            snippet = clean(text[start:end])
            print(f"IDAHO_PURCHASING_DIAG {pattern.upper()} {snippet[:900]}")


def collect() -> list[Opportunity]:
    html = http_get(URL)
    rows = parse_html(html)
    if not rows:
        _diagnose_dynamic_source(html)
    return rows
