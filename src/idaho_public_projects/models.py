from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Opportunity:
    id: str
    source: str
    title: str
    agency: str
    description: str = ""
    location: str = ""
    stage: str = "OPEN_BID"
    solicitation_type: str = ""
    solicitation_number: str = ""
    posted_date: str = ""
    open_date: str = ""
    due_date: str = ""
    updated_date: str = ""
    status: str = "OPEN"
    url: str = ""
    details_url: str = ""
    contact: str = ""
    category: str = "OTHER"
    score: int = 0
    estimated_value: float | None = None
    bidders: list[dict[str, Any]] = field(default_factory=list)
    first_seen: str = ""
    last_seen: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
