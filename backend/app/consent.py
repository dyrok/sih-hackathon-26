from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from .models import ConsentArtefact


VOLUNTARY_BUNDLES = {"checkin", "instruments", "passive", "unit_pulse"}


def active_consent(db: Session, pseudonym_id: str, bundle_id: str | None = None) -> ConsentArtefact | None:
    q = db.query(ConsentArtefact).filter(
        ConsentArtefact.principal_pseudonym == pseudonym_id,
        ConsentArtefact.withdrawn_at.is_(None),
    )
    if bundle_id:
        q = q.filter(ConsentArtefact.bundle_id == bundle_id)
    return q.order_by(ConsentArtefact.granted_at.desc()).first()


def has_voluntary_consent(db: Session, pseudonym_id: str) -> bool:
    row = (
        db.query(ConsentArtefact)
        .filter(
            ConsentArtefact.principal_pseudonym == pseudonym_id,
            ConsentArtefact.withdrawn_at.is_(None),
            ConsentArtefact.bundle_id.in_(list(VOLUNTARY_BUNDLES)),
        )
        .first()
    )
    return row is not None


def withdraw_all(db: Session, pseudonym_id: str, when: datetime) -> int:
    rows = (
        db.query(ConsentArtefact)
        .filter(
            ConsentArtefact.principal_pseudonym == pseudonym_id,
            ConsentArtefact.withdrawn_at.is_(None),
        )
        .all()
    )
    for r in rows:
        r.withdrawn_at = when
    return len(rows)
