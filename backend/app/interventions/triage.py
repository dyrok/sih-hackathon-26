from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import get_settings
from ..ids import nid
from ..models import AlertBudgetLedger, ResponseCase, TriageEntry, User

URGENCY_BASE = {"green": 0.0, "amber": 0.4, "red": 0.75, "critical": 1.0}


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _hours_open(case: ResponseCase) -> float:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return max(0.0, (now - case.opened_at).total_seconds() / 3600.0)


def urgency_of(case: ResponseCase) -> float:
    base = URGENCY_BASE.get(case.tier, 0.4)
    sla = case.sla_hours
    if sla is None:
        return base
    if sla <= 0:
        return 1.0
    pressure = min(1.0, _hours_open(case) / float(sla))
    return min(1.0, 0.6 * base + 0.4 * pressure)


def intervenability_of(db: Session, case: ResponseCase) -> float:
    counsellors = db.query(User).filter(User.role == "counsellor", User.is_active.is_(True)).count()
    slot = 1.0 if counsellors else 0.0
    coverage = 1.0 if case.unit_id else 0.6
    contactable = 0.8
    return 0.5 * slot + 0.3 * coverage + 0.2 * contactable


def _pick_counsellor(db: Session, as_of: date) -> tuple[str | None, bool, str | None]:
    """Returns (counsellor_id, deferred, reason). Critical always preempts cap."""
    settings = get_settings()
    cap = settings.counsellor_weekly_cap
    week = _week_start(as_of)
    counsellors = db.query(User).filter(User.role == "counsellor", User.is_active.is_(True)).all()
    if not counsellors:
        return None, True, "capacity_0"
    best = None
    best_used = 10**9
    for c in counsellors:
        ledger = (
            db.query(AlertBudgetLedger)
            .filter(AlertBudgetLedger.counsellor_id == c.id, AlertBudgetLedger.week_start == week)
            .one_or_none()
        )
        used = ledger.alerts_used if ledger else 0
        if used < best_used:
            best_used = used
            best = c
    assert best is not None
    if best_used >= cap:
        return best.id, True, "weekly_cap"
    ledger = (
        db.query(AlertBudgetLedger)
        .filter(AlertBudgetLedger.counsellor_id == best.id, AlertBudgetLedger.week_start == week)
        .one_or_none()
    )
    if ledger is None:
        ledger = AlertBudgetLedger(
            id=nid("bdg"),
            counsellor_id=best.id,
            week_start=week,
            alerts_used=0,
            cap=cap,
        )
        db.add(ledger)
        db.flush()
    ledger.alerts_used += 1
    return best.id, False, None


def upsert_triage(db: Session, case: ResponseCase) -> TriageEntry:
    settings = get_settings()
    as_of = case.opened_at.date()
    u = urgency_of(case)
    i = intervenability_of(db, case)
    priority = settings.triage_w_urgency * u + settings.triage_w_intervenability * i
    assigned, deferred, reason = _pick_counsellor(db, as_of)
    if case.tier == "critical":
        deferred = False
        reason = None if assigned else "capacity_0"
    existing = db.query(TriageEntry).filter(TriageEntry.case_id == case.id).one_or_none()
    if deferred and case.tier != "critical":
        case.status = "deferred"
    else:
        case.status = "open"
    if existing:
        existing.urgency = u
        existing.intervenability = i
        existing.priority = priority
        existing.assigned_counsellor_id = assigned
        existing.cap_reason = reason
        existing.deferred_until = (as_of + timedelta(days=1)) if deferred and case.tier != "critical" else None
        return existing
    entry = TriageEntry(
        id=nid("tr"),
        case_id=case.id,
        urgency=u,
        intervenability=i,
        priority=priority,
        deferred_until=(as_of + timedelta(days=1)) if deferred and case.tier != "critical" else None,
        assigned_counsellor_id=assigned,
        cap_reason=reason,
    )
    db.add(entry)
    db.flush()
    return entry


def ranked_queue(db: Session) -> list[tuple[ResponseCase, TriageEntry]]:
    rows = (
        db.query(ResponseCase, TriageEntry)
        .join(TriageEntry, TriageEntry.case_id == ResponseCase.id)
        .filter(ResponseCase.status.in_(["open", "deferred"]))
        .all()
    )
    rows.sort(key=lambda pair: (-pair[1].priority, pair[0].opened_at))
    return rows
