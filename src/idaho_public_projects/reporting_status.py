"""Additive, evidence-backed public projects reporting envelope."""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

SOURCES = {
    "City of Boise": ("boise", "City procurement portal", "event_opening"),
    "Idaho DPW": ("idaho-dpw", "State construction notices and bid results", None),
    "Idaho Purchasing": ("idaho-purchasing", "State-managed solicitation planning", "planning_record_update"),
    "Ada County": ("ada-county", "County procurement portal", None),
    "ACHD": ("achd", "Public OpenGov open solicitations", "solicitation_release"),
}

def as_date(raw):
    try:
        if not isinstance(raw, str) or len(raw) != 10:
            return None
        return date.fromisoformat(raw)
    except ValueError:
        return None


def source_date(label, row):
    if label == "City of Boise":
        return as_date(row.get("open_date"))
    if label == "Idaho Purchasing":
        return as_date(row.get("updated_date"))
    if label == "ACHD":
        return as_date(row.get("posted_date"))
    return None


def envelope(payload, current_status, previous_status, pre_run_ids):
    generated = payload["generated_at"]
    report_date = datetime.fromisoformat(generated.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Boise")).date()
    previous_envelope = previous_status.get("reporting_v1")
    previous_rows = previous_envelope.get("sources", []) if isinstance(previous_envelope, dict) else []
    prior = {x["id"]: x for x in previous_rows if isinstance(x, dict) and isinstance(x.get("id"), str)}
    legacy = {x.get("source"): x for x in previous_status.get("collector_status", []) if isinstance(x, dict)}
    statuses = {s["source"]: s for s in current_status["collector_status"]}
    measurements = []
    for label, (sid, coverage, kind) in SOURCES.items():
        before = prior.get(sid, {})
        previous_success = before.get("last_success_at") or (
            previous_status.get("generated_at") if not before and legacy.get(label, {}).get("status") == "OK" else None
        )
        status = statuses.get(label)
        raw = status["status"] if status else None
        source_rows = [x for x in payload["opportunities"] if x.get("source") == label]
        observed = [x for x in source_rows if x.get("last_seen") == generated] if raw == "OK" else []
        # Empty is a signal, not positive all-source closure; ACHD has explicit zero in its validated public payload.
        success = raw == "OK" or (label == "ACHD" and raw == "EMPTY")
        candidates = [d for r in observed if (d := source_date(label,r)) and d <= report_date]
        prior_date = as_date(before.get("latest_authoritative_date"))
        current_latest = max(candidates) if candidates else None
        if kind and prior_date and prior_date <= report_date:
            candidates.append(prior_date)
        latest = max(candidates) if candidates else None
        availability, outcome = ("reachable","success") if raw == "OK" else (
            ("reachable","no_data") if label == "ACHD" and raw == "EMPTY" else
            ("unknown","error") if raw == "ERROR" else
            ("unknown","unknown") if raw else ("not_attempted","unknown")
        )
        measurements.append({
            "id": sid, "label": label, "mode": "automatic", "coverage": coverage,
            "last_attempt_at": generated if status else None,
            "last_success_at": generated if success else previous_success,
            "latest_authoritative_date": latest.isoformat() if latest else None,
            "latest_date_kind": kind if latest else None,
            "date_provenance": ("current_source_observation" if latest == current_latest else "last_known_source_observation") if latest else None,
            "source_age_days": (report_date-latest).days if latest else None,
            "new_since_previous_success": sum(x["id"] not in pre_run_ids for x in observed) if success and previous_success is not None else None,
            "retained_records": len(source_rows), "observed_records": len(observed) if success else None,
            "availability": availability, "collection_outcome": outcome,
        })
    return {"schema_version": 1, "generated_at": generated, "sources": measurements}
