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

    for idx, table in enumerate(soup.find_all("table")):
        attrs = {k: v for k, v in table.attrs.items() if k == "id" or k == "class" or str(k).startswith("data-")}
        headers = [clean(x.get_text(" ", strip=True)) for x in table.find_all("th")]
        print(f"IDAHO_PURCHASING_DIAG TABLE index={idx} attrs={attrs} headers={headers}")

    for node in soup.find_all(attrs={"id": re.compile(r"tablepress|datatable", re.I)}):
        print(f"IDAHO_PURCHASING_DIAG NODE tag={node.name} attrs={node.attrs}")

    for script in soup.find_all("script"):
        src = script.get("src")
        if src and ("tablepress" in src.lower() or "datatable" in src.lower()):
            print(f"IDAHO_PURCHASING_DIAG SCRIPT {urljoin(URL, src)}")
        inline = script.string or script.get_text(" ", strip=True)
        if inline and any(x in inline.lower() for x in ("tablepress", "datatable", "ajax")):
            print(f"IDAHO_PURCHASING_DIAG INLINE {clean(inline)[:2500]}")

    text = html.replace("\n", " ")
    for pattern in [r"tablepress[-_][A-Za-z0-9_-]+", r"data-[A-Za-z0-9_-]+=['\"][^'\"]+", r"ajax[^,;<]{0,180}"]:
        matches = []
        for match in re.finditer(pattern, text, re.I):
            value = clean(match.group(0))
            if value not in matches:
                matches.append(value)
            if len(matches) >= 20:
                break
        for value in matches:
            print(f"IDAHO_PURCHASING_DIAG MATCH {value[:700]}")


def collect() -> list[Opportunity]:
    html = http_get(URL)
    rows = parse_html(html)
    if not rows:
        _diagnose_dynamic_source(html)
    return rows
