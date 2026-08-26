from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, stable_id

URL = "https://www.achdidaho.org/community-resources/street-services/public-notices"
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_RE = re.compile(rf"{MONTH}\s+\d{{1,2}},\s+\d{{4}}", re.I)


def _body_for_heading(heading: Tag) -> str:
    node = heading
    for _ in range(5):
        node = node.parent
        if node is None:
            break
        classes = " ".join(node.get("class", [])).lower() if isinstance(node, Tag) else ""
        if any(k in classes for k in ("accordion", "notice", "item")):
            text = clean(node.get_text(" ", strip=True))
            if len(text) > len(clean(heading.get_text(" ", strip=True))) + 40:
                return text
    parts: list[str] = []
    for sib in heading.next_siblings:
        if isinstance(sib, Tag) and sib.name in {"h2", "h3", "h4"}:
            break
        if isinstance(sib, Tag):
            value = clean(sib.get_text(" ", strip=True))
            if value:
                parts.append(value)
        if sum(map(len, parts)) > 7000:
            break
    return clean(" ".join(parts))


def parse_html(html: str) -> list[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[Opportunity] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = clean(heading.get_text(" ", strip=True))
        dates = DATE_RE.findall(heading_text)
        if not dates or " - " not in heading_text:
            continue
        title = heading_text.split(" - ")[-1].strip()
        if len(title) < 4:
            continue

        body = _body_for_heading(heading)
        combined = clean(f"{heading_text} {body}")
        posted = parse_date(dates[0])
        due = parse_date(dates[-1])
        due_match = re.search(
            rf"(?:until|before|by)\s+[^.]*?({MONTH}\s+\d{{1,2}},\s+\d{{4}})",
            body,
            re.I,
        )
        if due_match:
            due = parse_date(due_match.group(1))

        type_match = re.search(
            r"\b(REQUEST FOR PROPOSAL|INVITATION TO BID|REQUEST FOR QUALIFICATIONS|REQUEST FOR QUOTE)\b",
            combined, re.I,
        )
        stype = {
            "REQUEST FOR PROPOSAL": "RFP",
            "INVITATION TO BID": "ITB",
            "REQUEST FOR QUALIFICATIONS": "RFQ",
            "REQUEST FOR QUOTE": "RFQ",
        }.get(type_match.group(1).upper(), "") if type_match else ""
        number_match = re.search(
            r"(?:Contract Number|Project Number|RFP|ITB)?\s*:?\s*\b([A-Z]{1,4}\d{2,4}-\d{1,3})\b",
            combined,
        )
        number = number_match.group(1) if number_match else ""
        location_match = re.search(r"Project Location:\s*([^.;]+)", combined, re.I)
        location = clean(location_match.group(1)) if location_match else "Ada County, Idaho"

        open_url = URL
        container = heading.parent
        if container:
            for link in container.find_all("a", href=True):
                href = link["href"]
                if "procurement.opengov.com" in href:
                    open_url = href
                    break

        results.append(
            Opportunity(
                id=stable_id("achd", number, title),
                source="ACHD",
                title=title,
                agency="Ada County Highway District",
                description=body[:6000],
                location=location,
                stage="OPEN_BID",
                solicitation_type=stype,
                solicitation_number=number,
                posted_date=posted,
                due_date=due,
                status="OPEN",
                url=open_url,
                details_url=open_url if open_url != URL else "",
            )
        )
    return results


def collect() -> list[Opportunity]:
    return parse_html(http_get(URL))
