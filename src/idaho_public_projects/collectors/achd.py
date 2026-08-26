from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, stable_id

NOTICE_URL = "https://www.achdidaho.org/community-resources/street-services/public-notices"
PROCUREMENT_URL = "https://www.achdidaho.org/projects/bids-procurement"
URL = "https://procurement.opengov.com/portal/embed/achdidaho/project-list?departmentId=all&status=open"
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_RE = re.compile(rf"{MONTH}\s+\d{{1,2}},\s+\d{{4}}", re.I)


def _parse_opengov_table(soup: BeautifulSoup) -> list[Opportunity]:
    results: list[Opportunity] = []
    for table in soup.find_all("table"):
        headers = [clean(x.get_text(" ", strip=True)).lower() for x in table.find_all("th")]
        header_text = " ".join(headers)
        if "project title" not in header_text or "due date" not in header_text:
            continue

        for row in table.find_all("tr"):
            cells = [clean(c.get_text(" ", strip=True)) for c in row.find_all("td")]
            if not cells:
                continue
            title = cells[0]
            if not title or title.lower() == "project title":
                continue

            number = ""
            status = "OPEN"
            posted = ""
            due = ""
            if len(cells) >= 6:
                number, status, posted, due = cells[1], cells[2], cells[-2], cells[-1]
            elif len(cells) >= 5:
                status, posted, due = cells[1], cells[-2], cells[-1]
            elif len(cells) >= 3:
                status, due = cells[1], cells[-1]

            if status.lower() not in {"open", "active", "pending", "closed"} and not parse_date(due):
                continue

            link = row.find("a", href=True)
            href = urljoin("https://procurement.opengov.com", link["href"]) if link else URL
            if "/portal/embed/" in href:
                href = href.replace("/portal/embed/", "/portal/")

            results.append(
                Opportunity(
                    id=stable_id("achd", number, title),
                    source="ACHD",
                    title=title,
                    agency="Ada County Highway District",
                    description=f"ACHD OpenGov procurement project. Status: {status}.",
                    location="Ada County, Idaho",
                    stage="OPEN_BID" if status.lower() in {"open", "active", "pending"} else "CLOSED",
                    solicitation_type="PROCUREMENT",
                    solicitation_number=number,
                    posted_date=parse_date(posted),
                    due_date=parse_date(due),
                    status=status.upper() or "OPEN",
                    url=href,
                    details_url=href if href != URL else "",
                )
            )
    return results


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


def _parse_notice_page(soup: BeautifulSoup) -> list[Opportunity]:
    results: list[Opportunity] = []
    seen: set[str] = set()
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
            combined,
            re.I,
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
        bonding_match = re.search(r"Expected Contract Bonding Requirement:\s*\$?([\d,]+(?:\.\d{1,2})?)", combined, re.I)
        if bonding_match:
            body = clean(f"{body} Expected contract bonding requirement: ${bonding_match.group(1)}.")

        open_url = NOTICE_URL
        container = heading.parent
        if container:
            for link in container.find_all("a", href=True):
                href = link["href"]
                if "procurement.opengov.com" in href:
                    open_url = href
                    break

        oid = stable_id("achd", number, title)
        if oid in seen:
            continue
        seen.add(oid)
        results.append(
            Opportunity(
                id=oid,
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
                details_url=open_url if open_url != NOTICE_URL else "",
            )
        )
    return results


def parse_html(html: str) -> list[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    rows = _parse_notice_page(soup)
    return rows if rows else _parse_opengov_table(soup)


def _browser_get(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": PROCUREMENT_URL,
            "Cache-Control": "no-cache",
        },
        timeout=35,
    )
    response.raise_for_status()
    return response.text


def collect() -> list[Opportunity]:
    # ACHD's own public notices contain materially richer project intelligence
    # than OpenGov's client-rendered list, so prefer that source. If the site
    # rejects the GitHub runner or changes shape, fail soft to OpenGov.
    try:
        rows = parse_html(_browser_get(NOTICE_URL))
        if rows:
            return rows
    except requests.RequestException:
        pass
    return parse_html(http_get(URL))
