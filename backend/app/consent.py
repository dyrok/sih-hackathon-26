from __future__ import annotations

import hashlib
import json
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


def artefact_hash(
    *,
    principal: str,
    bundle_id: str,
    purpose: str,
    categories: list[str],
    language: str,
    version: str,
    granted_at: datetime,
) -> str:
    """A consent artefact has to be able to prove what was agreed to.

    The hash was previously a random id, which meant the artefact recorded that
    consent happened but not to what — so a later edit of the purpose string or
    the category list left no trace (TC-449). Hashing the canonical content
    makes the artefact self-verifying.
    """
    body = json.dumps(
        {
            "principal": principal,
            "bundle_id": bundle_id,
            "purpose": purpose,
            "categories": sorted(categories),
            "language": language,
            "version": version,
            "granted_at": granted_at.isoformat(),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def verify_artefact(row) -> bool:
    """True when the stored artefact still matches its recorded content."""
    return row.artefact_hash == artefact_hash(
        principal=row.principal_pseudonym,
        bundle_id=row.bundle_id,
        purpose=row.purpose_string,
        categories=list(row.data_categories or []),
        language=row.language,
        version=row.consent_version,
        granted_at=row.granted_at,
    )
