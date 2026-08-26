from __future__ import annotations

from datetime import date, datetime

from .models import Opportunity


BUILDING = (
    "building", "facility", "remodel", "renovation", "roof", "hvac", "heating", "cooling",
    "fire alarm", "elevator", "window", "door", "plumbing", "electrical", "mechanical",
    "envelope", "interior", "restroom", "campus", "construction",
)
CIVIL = (
    "bridge", "road", "roadway", "signal", "pavement", "sewer", "water", "utility",
    "roundabout", "sidewalk", "drainage", "intersection", "street",
)
MATERIAL = ("pump", "equipment", "material", "supply", "parts", "vehicle", "generator")
PROFESSIONAL = ("engineering services", "architect", "consulting", "consultant", "design services")
TREASURE_VALLEY = ("boise", "meridian", "nampa", "caldwell", "eagle", "kuna", "star", "garden city", "ada county")


def classify(op: Opportunity) -> Opportunity:
    text = f"{op.title} {op.description} {op.location}".lower()
    if any(k in text for k in BUILDING):
        op.category = "BUILDING"
    elif any(k in text for k in CIVIL):
        op.category = "CIVIL"
    elif any(k in text for k in MATERIAL):
        op.category = "MATERIALS_EQUIPMENT"
    elif any(k in text for k in PROFESSIONAL):
        op.category = "PROFESSIONAL_SERVICES"
    else:
        op.category = "OTHER"

    score = 25
    if any(k in text for k in TREASURE_VALLEY):
        score += 20
    if op.category == "BUILDING":
        score += 25
    elif op.category == "CIVIL":
        score += 18
    elif op.category == "MATERIALS_EQUIPMENT":
        score += 15
    elif op.category == "PROFESSIONAL_SERVICES":
        score += 8

    if op.stage in {"FUTURE", "UPCOMING", "DESIGN_RFP", "DESIGN_RFQ"}:
        score += 15
    if op.stage == "OPEN_BID":
        score += 8
    if op.details_url:
        score += 4
    if op.estimated_value and op.estimated_value >= 500_000:
        score += 8

    if op.due_date:
        try:
            days = (datetime.strptime(op.due_date, "%Y-%m-%d").date() - date.today()).days
            if 0 <= days <= 14:
                score += 8
            elif 15 <= days <= 30:
                score += 4
            elif days < 0 and op.stage == "OPEN_BID":
                op.stage = "CLOSED"
                op.status = "CLOSED"
        except ValueError:
            pass

    op.score = max(0, min(100, score))
    return op
