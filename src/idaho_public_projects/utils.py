from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from email.utils import parsedate_to_datetime

import requests


USER_AGENT = "IdahoPublicProjectIntelligence/0.1 (+https://github.com/destrynielsen-maker)"


def stable_id(source: str, number: str, title: str) -> str:
    key = "|".join([source.strip().lower(), number.strip().lower(), title.strip().lower()])
    return f"{source.lower()}-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:16]}"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def parse_date(value: str) -> str:
    raw = clean(value)
    if not raw:
        return ""
    raw = re.sub(r"\b(?:MST|MDT|PST|PDT|UTC)\b", "", raw).strip()
    candidates = [
        raw,
        raw.split(",", 1)[0] if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4},", raw) else raw,
    ]
    formats = (
        "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y",
        "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d",
    )
    for candidate in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(candidate.strip(), fmt).date().isoformat()
            except ValueError:
                pass
    match = re.search(
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})",
        raw,
        re.I,
    )
    if match:
        try:
            return datetime.strptime(match.group(1), "%B %d, %Y").date().isoformat()
        except ValueError:
            pass
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except Exception:
        return ""


def parse_money(text: str) -> float | None:
    match = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", text or "")
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def http_get(url: str, timeout: int = 35) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


def today_iso() -> str:
    return date.today().isoformat()
