from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of
from ...db import get_db
from ...firewall import forbid_commander
from ...models import MaskingFlag, RiskFactor, RiskScore, User
from ...risk.explainer import top_factors
from ...risk.scorer import recompute_many
from ...security import require_roles

router = APIRouter(tags=["risk"])


class RecomputeIn(BaseModel):
    pseudonyms: list[str] | None = None
    full: bool = False


def _latest(db: Session, pid: str) -> RiskScore:
    row = (
        db.query(RiskScore)
        .filter(RiskScore.pseudonym_id == pid)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )
    if row is None:
        raise HTTPException(404, "no score")
    return row


@router.post("/risk/recompute")
def recompute(
    body: RecomputeIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "counsellor", "hr_ingest")),
):
    forbid_commander(user, db=db, resource_type="risk")
    pids = None if body.full else body.pseudonyms
    n = recompute_many(db, pids, as_of=as_of())
    write_audit(db, actor=user, action="risk.recompute", resource_type="risk_score", payload={"n": n})
    return {"recomputed": n}


@router.get("/risk/{pseudonym_id}")
def get_risk(
    pseudonym_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="risk", resource_id=pseudonym_id)
    row = _latest(db, pseudonym_id)
    factors = db.query(RiskFactor).filter(RiskFactor.score_id == row.id).all()
    mask = db.query(MaskingFlag).filter(MaskingFlag.score_id == row.id).one_or_none()
    write_audit(
        db,
        actor=user,
        action="risk.read",
        resource_type="risk_score",
        resource_id=row.id,
        subject_pseudonym_id=pseudonym_id,
        purpose="case_review",
        reason="counsellor/welfare case view",
    )
    return {
        "pseudonym_id": pseudonym_id,
        "score": row.score,
        "tier": row.tier,
        "confidence": row.confidence,
        "sources_present": row.sources_present,
        "masking": bool(mask),
        "engine_version": row.engine_version,
        "ruleset_version": row.ruleset_version,
        "as_of": row.as_of.isoformat(),
        "factors": [
            {"rule_id": f.rule_id, "key": f.display_key, "value": f.display_value, "weight": f.weight}
            for f in factors
        ],
    }


@router.get("/risk/{pseudonym_id}/explanation")
def explanation(
    pseudonym_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("counsellor", "welfare_officer")),
):
    forbid_commander(user, db=db, resource_type="risk", resource_id=pseudonym_id)
    row = _latest(db, pseudonym_id)
    factors = db.query(RiskFactor).filter(RiskFactor.score_id == row.id).all()
    mask = db.query(MaskingFlag).filter(MaskingFlag.score_id == row.id).one_or_none()
    payload = [
        {
            "rule_id": f.rule_id,
            "display_key": f.display_key,
            "observed_value": f.observed_value,
            "weight": f.weight,
        }
        for f in factors
    ]
    write_audit(
        db,
        actor=user,
        action="risk.explanation",
        resource_type="risk_score",
        resource_id=row.id,
        subject_pseudonym_id=pseudonym_id,
        purpose="case_review",
        reason="top-3 factors",
    )
    return {
        "pseudonym_id": pseudonym_id,
        "score": row.score,
        "tier": row.tier,
        "confidence": row.confidence,
        "top_factors": top_factors(payload, n=3),
        "masking": bool(mask),
        "engine_version": row.engine_version,
        "ruleset_version": row.ruleset_version,
    }
