from __future__ import annotations

import re

import requests

from ..models import Opportunity
from ..utils import stable_id

PORTAL_URL = "https://adacounty.bonfirehub.com/portal"
API_URL = "https://adacounty.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData"


def _date_only(value: str) -> str:
    value = str(value or "").strip()
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", value)
    return match.group(1) if match else ""


def _type_from_reference(reference: str) -> str:
    ref = (reference or "").strip().upper()
    for kind in ("RFP", "RFQ", "RFI", "ITB", "BID"):
        if ref.startswith(kind):
            return kind
    return "PROCUREMENT"


def parse_report(payload: dict) -> list[Opportunity]:
    projects = ((payload or {}).get("payload") or {}).get("projects") or {}
    if isinstance(projects, list):
        iterable = projects
    elif isinstance(projects, dict):
        iterable = projects.values()
    else:
        return []

    rows: list[Opportunity] = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        project_id = str(item.get("ProjectID") or "").strip()
        title = str(item.get("ProjectName") or "").strip()
        reference = str(item.get("ReferenceID") or "").strip()
        if not project_id or not title:
            continue

        details = f"https://adacounty.bonfirehub.com/opportunities/{project_id}"
        rows.append(
            Opportunity(
                id=stable_id("ada-county", reference or project_id, title),
                source="Ada County",
                title=title,
                agency="Ada County",
                description=f"Ada County public procurement opportunity: {title}",
                location="Ada County, Idaho",
                stage="OPEN_BID",
                solicitation_type=_type_from_reference(reference),
                solicitation_number=reference,
                due_date=_date_only(item.get("DateClose") or ""),
                status="OPEN",
                url=details,
                details_url=details,
            )
        )
    return rows


def collect() -> list[Opportunity]:
    response = requests.get(
        API_URL,
        headers={
            "User-Agent": "IdahoPublicProjectIntelligence/0.1 (+https://github.com/destrynielsen-maker)",
            "Accept": "application/json, text/plain, */*",
        },
        timeout=35,
    )
    response.raise_for_status()
    return parse_report(response.json())
