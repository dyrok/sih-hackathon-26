from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..ids import nid
from ..models import ResponseCase, RiskScore
from .ladder import SLA
from .triage import upsert_triage


def open_or_update_case(
    db: Session,
    pseudonym_id: str,
    score: RiskScore,
    unit_id: str | None = None,
) -> ResponseCase:
    existing = (
        db.query(ResponseCase)
        .filter(
            ResponseCase.pseudonym_id == pseudonym_id,
            ResponseCase.group_case.is_(False),
            ResponseCase.status.in_(["open", "deferred"]),
        )
        .one_or_none()
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    sla = SLA.get(score.tier)
    if existing:
        existing.score_id = score.id
        existing.tier = score.tier
        existing.unit_id = unit_id or existing.unit_id
        existing.sla_hours = sla
        db.flush()
        upsert_triage(db, existing)
        return existing
    case = ResponseCase(
        id=nid("cs"),
        pseudonym_id=pseudonym_id,
        score_id=score.id,
        unit_id=unit_id,
        tier=score.tier,
        opened_at=now,
        status="open",
        group_case=False,
        sla_hours=sla,
    )
    db.add(case)
    db.flush()
    upsert_triage(db, case)
    return case


def open_group_case(db: Session, *, unit_id: str | None, incident_id: str, score_id: str | None) -> ResponseCase:
    existing = (
        db.query(ResponseCase)
        .filter(
            ResponseCase.group_case.is_(True),
            ResponseCase.incident_id == incident_id,
            ResponseCase.status.in_(["open", "deferred"]),
        )
        .one_or_none()
    )
    if existing:
        return existing
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    case = ResponseCase(
        id=nid("gcs"),
        pseudonym_id=None,
        score_id=score_id,
        unit_id=unit_id,
        tier="red",
        opened_at=now,
        status="open",
        group_case=True,
        incident_id=incident_id,
        sla_hours=24,
    )
    db.add(case)
    db.flush()
    upsert_triage(db, case)
    return case
