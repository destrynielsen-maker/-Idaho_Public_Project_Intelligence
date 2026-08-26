from __future__ import annotations

import re
from bs4 import BeautifulSoup

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, stable_id

URL = "https://bids.sciquest.com/apps/Router/PublicEvent?CustomerOrg=CityofBoise"


def _container_text(anchor) -> tuple[str, object]:
    row = anchor.find_parent("tr")
    if row is not None:
        return clean(row.get_text(" ", strip=True)), row
    node = anchor.parent
    for _ in range(6):
        if node is None:
            break
        text = clean(node.get_text(" ", strip=True))
        if "Open" in text and "Close" in text:
            return text, node
        node = node.parent
    return clean(anchor.parent.get_text(" ", strip=True)), anchor.parent


def parse_html(html: str) -> list[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[Opportunity] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        event_href = anchor.get("href", "")
        if "jaggaer.com" not in event_href or "app" not in event_href:
            continue
        title = clean(anchor.get_text(" ", strip=True))
        if not title or title.lower().startswith("http"):
            continue
        text, container = _container_text(anchor)
        if "Close" not in text and "Open" not in text:
            continue

        open_match = re.search(r"\bOpen\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.I)
        close_match = re.search(r"\bClose\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.I)
        type_match = re.search(r"\bType\s+([A-Za-z0-9-]+)", text)
        number_match = re.search(r"\bNumber\s+([A-Za-z0-9-]+)", text)
        emails = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)))

        description = text
        if title in description:
            description = clean(description.replace(title, "", 1))
        marker = re.search(r"\bOpen\s+\d{1,2}/\d{1,2}/\d{4}", description, re.I)
        if marker:
            description = clean(description[: marker.start()])

        number = number_match.group(1) if number_match else ""
        oid = stable_id("boise", number, title)
        if oid in seen:
            continue
        seen.add(oid)
        results.append(
            Opportunity(
                id=oid,
                source="City of Boise",
                title=title,
                agency="City of Boise",
                description=description,
                location="Boise, Idaho",
                stage="OPEN_BID",
                solicitation_type=(type_match.group(1).upper() if type_match else ""),
                solicitation_number=number,
                open_date=parse_date(open_match.group(1) if open_match else ""),
                posted_date=parse_date(open_match.group(1) if open_match else ""),
                due_date=parse_date(close_match.group(1) if close_match else ""),
                status="OPEN",
                # JAGGAER generates signed event/PDF URLs that can expire. Keep the
                # permanent City public-event index as the canonical link so RSS and
                # dashboard entries remain usable over time. The current event URL is
                # retained as auxiliary detail and is refreshed every collection run.
                url=URL,
                details_url=event_href,
                contact=", ".join(emails),
            )
        )
    return results


def collect() -> list[Opportunity]:
    return parse_html(http_get(URL))
