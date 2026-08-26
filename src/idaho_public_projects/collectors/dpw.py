from __future__ import annotations

import re
from bs4 import BeautifulSoup

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, parse_money, stable_id

URL = "https://dpw.idaho.gov/construction/"


def _find_heading(soup: BeautifulSoup, phrase: str):
    phrase = phrase.lower()
    for heading in soup.find_all(["h2", "h3", "h4"]):
        if phrase in clean(heading.get_text(" ", strip=True)).lower():
            return heading
    return None


def _location(title: str) -> str:
    match = re.search(r",\s*([^,]+),\s*Idaho\b", title, re.I)
    return f"{clean(match.group(1))}, Idaho" if match else ""


def parse_html(html: str) -> list[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[Opportunity] = []

    heading = _find_heading(soup, "Advertisement for Bid")
    table = heading.find_next("table") if heading else None
    if table:
        for row in table.find_all("tr"):
            cells = [clean(c.get_text(" ", strip=True)) for c in row.find_all(["td", "th"])]
            if len(cells) < 3 or cells[0].lower().startswith("bid date"):
                continue
            bid_date, number, title = cells[0], cells[1], cells[2]
            if not re.search(r"\d{1,2}-\d{1,2}-\d{2,4}", bid_date):
                continue
            link = row.find("a", href=True)
            results.append(
                Opportunity(
                    id=stable_id("dpw", number, title),
                    source="Idaho DPW",
                    title=title,
                    agency="Idaho Division of Public Works",
                    description=title,
                    location=_location(title),
                    stage="OPEN_BID",
                    solicitation_type="CONSTRUCTION_BID",
                    solicitation_number=number,
                    due_date=parse_date(bid_date),
                    status="OPEN",
                    url=(link["href"] if link else URL),
                    details_url=(link["href"] if link else ""),
                )
            )

    results_heading = _find_heading(soup, "Recent Construction Bid Results")
    results_table = results_heading.find_next("table") if results_heading else None
    if results_table:
        current: dict | None = None

        def flush():
            nonlocal current
            if not current:
                return
            bidders = current.get("bidders", [])
            desc = "Bid results: " + "; ".join(
                f"{b.get('contractor','')}{' — $'+format(b['base_bid'], ',.0f') if b.get('base_bid') is not None else ''}"
                for b in bidders[:12]
            )
            values = [b["base_bid"] for b in bidders if b.get("base_bid") is not None]
            results.append(
                Opportunity(
                    id=stable_id("dpw-result", current["number"], current["title"]),
                    source="Idaho DPW",
                    title=current["title"],
                    agency="Idaho Division of Public Works",
                    description=desc,
                    location=_location(current["title"]),
                    stage="BID_RESULTS",
                    solicitation_type="BID_RESULT",
                    solicitation_number=current["number"],
                    due_date=parse_date(current["date"]),
                    status="RESULTS",
                    url=current.get("url") or URL,
                    details_url=current.get("url") or "",
                    estimated_value=min(values) if values else None,
                    bidders=bidders,
                )
            )
            current = None

        for row in results_table.find_all("tr"):
            cells = [clean(c.get_text(" ", strip=True)) for c in row.find_all(["td", "th"])]
            if not cells or cells[0].lower() in {"date", "submission date"}:
                continue
            first = cells[0]
            is_new = bool(re.search(r"\d{1,2}-\d{1,2}-\d{2,4}", first))
            if is_new and len(cells) >= 4:
                flush()
                link = row.find("a", href=True)
                current = {
                    "date": cells[0],
                    "number": cells[1] if len(cells) > 1 else "",
                    "title": cells[2] if len(cells) > 2 else "",
                    "url": link["href"] if link else URL,
                    "bidders": [],
                }
                contractor = cells[3] if len(cells) > 3 else ""
                bid = parse_money(cells[4]) if len(cells) > 4 else None
                if contractor:
                    current["bidders"].append({"contractor": contractor, "base_bid": bid})
            elif current:
                contractor = cells[0] if cells else ""
                bid = parse_money(cells[1]) if len(cells) > 1 else None
                if contractor:
                    current["bidders"].append({"contractor": contractor, "base_bid": bid})
        flush()

    return results


def collect() -> list[Opportunity]:
    return parse_html(http_get(URL))
