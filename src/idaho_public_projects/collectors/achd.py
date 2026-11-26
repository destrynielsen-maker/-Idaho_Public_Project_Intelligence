from __future__ import annotations

import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from ..models import Opportunity
from ..utils import clean, http_get, parse_date, stable_id

NOTICE_URL = "https://www.achdidaho.org/community-resources/street-services/public-notices"
URL = "https://procurement.opengov.com/portal/embed/achdidaho/project-list?departmentId=all&status=open"
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_RE = re.compile(rf"{MONTH}\s+\d{{1,2}},\s+\d{{4}}", re.I)


def _parse_opengov_table(soup: BeautifulSoup) -> list[Opportunity]:
    """Parse OpenGov's public project-list table.

    The public embed is preferred over ACHD's own public-notice page because
    ACHD currently blocks GitHub-hosted HTTP clients with a 403 response.
    """
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

            # OpenGov commonly renders: Project Title | Project ID | Status |
            # Addenda | Release Date | Due Date. Some portals omit Project ID.
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

            # Reject UI rows and anything that does not carry a real project date/status.
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
    """Fallback parser retained for saved fixtures and if ACHD relaxes blocking."""
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

        open_url = NOTICE_URL
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
                details_url=open_url if open_url != NOTICE_URL else "",
            )
        )
    return results


def _local_og_date(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("ACHD OpenGov project date missing or invalid")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("ACHD OpenGov project date lacks a time zone")
    return date.astimezone(ZoneInfo("America/Boise")).date().isoformat()


MAX_OPEN_PAGES = 10
MAX_OPEN_ROWS = 100
MAX_STATUS_CHECKS = 8


def _public_embedded_objects(soup: BeautifulSoup, key: str) -> list[dict]:
    # Public page hydration, not a private API. Never execute the script.
    objects = []
    for script in soup.find_all("script"):
        text = str(script.string or "").lstrip()
        if not text.startswith("window.__data="):
            continue
        for match in re.finditer(rf'"{re.escape(key)}"\s*:\s*(?=\{{)', text):
            try:
                value, _ = json.JSONDecoder().raw_decode(text, match.end())
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                objects.append(value)
    return objects


def _public_page(soup: BeautifulSoup) -> tuple[int, list[dict]] | None:
    lists = [item for item in _public_embedded_objects(soup, "govProjects") if {"count", "rows"} <= item.keys()]
    if not lists:
        return None
    if len(lists) != 1:
        raise ValueError("ACHD OpenGov public project list is ambiguous")
    count, rows = lists[0]["count"], lists[0]["rows"]
    if type(count) is not int or not isinstance(rows, list) or not len(rows) <= count <= MAX_OPEN_ROWS:
        raise ValueError("ACHD OpenGov public open-list count/rows invalid or above safe cap")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("ACHD OpenGov project row is invalid")
    return count, rows


def _opportunities(rows: list[dict]) -> list[Opportunity]:
    results = []
    portal_ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ACHD OpenGov project row is invalid")
        if (
            row.get("government", {}).get("code") != "achdidaho"
            or row.get("status") != "open"
            or row.get("isPrivate") is not False
            or row.get("isPaused") is not False
            or row.get("comingSoon") is not False
        ):
            raise ValueError("ACHD OpenGov returned an unexpected non-public/open row")
        project_id = row.get("id")
        title = clean(row.get("title"))
        number = clean(row.get("financialId"))
        if type(project_id) is not int or project_id < 1 or not title or project_id in portal_ids:
            raise ValueError("ACHD OpenGov project ID/title missing or duplicated")
        portal_ids.add(project_id)
        posted = _local_og_date(row.get("releaseProjectDate"))
        due = _local_og_date(row.get("proposalDeadline"))
        if due < posted:
            raise ValueError("ACHD OpenGov deadline precedes release")
        kind = clean((row.get("template") or {}).get("title")).lower()
        kind = {
            "request for proposal": "RFP",
            "request for qualifications": "RFQ",
            "request for quote": "RFQ",
            "invitation to bid": "ITB",
        }.get(kind, "PROCUREMENT")
        url = f"https://procurement.opengov.com/portal/achdidaho/projects/{project_id}"
        description = clean(BeautifulSoup(row.get("summary") or "", "html.parser").get_text(" ", strip=True))
        results.append(Opportunity(
            id=stable_id("achd", number, title),
            source="ACHD",
            title=title,
            agency="Ada County Highway District",
            description=(description or "ACHD OpenGov procurement project.")[:6000],
            location="Ada County, Idaho",
            stage="OPEN_BID",
            solicitation_type=kind,
            solicitation_number=number,
            posted_date=posted,
            due_date=due,
            status="OPEN",
            url=url,
            details_url=url,
        ))
    if len({row.id for row in results}) != len(results):
        raise ValueError("ACHD OpenGov rows collide under the existing history key")
    return results


def parse_html(html: str) -> list[Opportunity]:
    soup = BeautifulSoup(html, "html.parser")
    page = _public_page(soup)
    if page is not None:
        count, rows = page
        if count != len(rows):
            raise ValueError("ACHD standalone parser requires a complete open list")
        return _opportunities(rows)
    rows = _parse_opengov_table(soup)
    return rows if rows else _parse_notice_page(soup)


def collect() -> list[Opportunity]:
    soup = BeautifulSoup(http_get(URL), "html.parser")
    first = _public_page(soup)
    if first is None:
        legacy = _parse_opengov_table(soup)
        if legacy:
            return legacy
        raise ValueError("ACHD OpenGov returned neither a public project payload nor recognized project rows")
    count, first_rows = first
    rows = list(first_rows)
    pages = 1
    while len(rows) < count:
        if pages >= MAX_OPEN_PAGES:
            raise ValueError("ACHD OpenGov pagination exceeded safe page limit")
        pages += 1
        page = _public_page(BeautifulSoup(http_get(f"{URL}&page={pages}"), "html.parser"))
        if page is None or page[0] != count or not page[1] or len(rows) + len(page[1]) > count:
            raise ValueError("ACHD OpenGov pagination incomplete or count changed")
        rows.extend(page[1])
    if pages > 1:
        repeat = _public_page(BeautifulSoup(http_get(URL), "html.parser"))
        # Compare IDs and all publication fields we rely on, not unrelated metadata.
        keys = ("id", "title", "financialId", "status", "isPrivate", "isPaused", "comingSoon", "releaseProjectDate", "proposalDeadline")
        fingerprint = lambda items: [tuple(row.get(key) for key in keys) for row in items]
        if repeat is None or repeat[0] != count or fingerprint(repeat[1]) != fingerprint(first_rows):
            raise ValueError("ACHD OpenGov pagination first page changed during scan")
    return _opportunities(rows)


def _canonical_id(url: object) -> int | None:
    match = re.fullmatch(r"https://procurement\.opengov\.com/portal/achdidaho/projects/([1-9][0-9]*)", url) if isinstance(url, str) else None
    return int(match[1]) if match else None


def parse_status_observation(html: str, portal_id: int) -> tuple[str, str | None]:
    objects = _public_embedded_objects(BeautifulSoup(html, "html.parser"), "project")
    exact = [
        row for row in objects
        if type(row.get("id")) is int and row["id"] == portal_id
        and isinstance(row.get("government"), dict) and row["government"].get("code") == "achdidaho"
        and row.get("isPrivate") is False
    ]
    if len(exact) != 1:
        return "UNVERIFIED", None
    status, substatus = exact[0].get("status"), exact[0].get("closedSubstatus")
    if status not in {"open", "evaluation", "awardPending", "closed"}:
        return "UNVERIFIED", None
    if substatus is not None and (not isinstance(substatus, str) or not re.fullmatch(r"[A-Za-z]{1,30}", substatus)):
        return "UNVERIFIED", None
    return status, substatus


def observe_missing(history: list[dict], current: list[Opportunity]) -> list[dict]:
    # Observations are read-only sidecars. They do not edit visible stage/status,
    # last_seen, or first_seen and are not passed to the publishing pipeline.
    now = datetime.now(ZoneInfo("UTC")).replace(microsecond=0).isoformat()
    live = {_canonical_id(item.url) for item in current}
    output = []
    checked = set()
    for saved in history:
        if saved.get("source") != "ACHD" or saved.get("stage") != "OPEN_BID":
            continue
        url = saved.get("details_url") or saved.get("url")
        pid = _canonical_id(url)
        if pid is None or pid in live or pid in checked:
            continue
        if len(checked) >= MAX_STATUS_CHECKS:
            break
        checked.add(pid)
        try:
            state, sub = parse_status_observation(http_get(url), pid)
            reason = "DIRECT_PUBLIC_DETAIL" if state != "UNVERIFIED" else "DETAIL_NOT_VERIFIED"
        except Exception:
            state, sub, reason = "UNVERIFIED", None, "DETAIL_UNAVAILABLE"
        output.append({
            "id": saved.get("id"), "portal_project_id": pid, "status_observed": state,
            "closed_substatus_observed": sub, "source_url": url, "reason": reason,
            "observed_at": now, "publication_effect": "NONE",
        })
    return output
