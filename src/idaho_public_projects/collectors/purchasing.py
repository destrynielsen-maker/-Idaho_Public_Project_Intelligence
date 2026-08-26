from __future__ import annotations

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


def collect() -> list[Opportunity]:
    return parse_html(http_get(URL))
