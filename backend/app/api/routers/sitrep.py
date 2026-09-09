"""Officer voice sitrep — self-scope duty log with a private wellness hint.

The transcript is the work product. Tone/mood are a heuristic larp on the
same utterance, returned only to the signed-in officer. No subject selector,
so this cannot become a channel for anyone else's welfare data (ADR-0003).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of
from ...db import get_db
from ...ids import nid
from ...models import DutySitrep, User
from ...security import require_roles
from ...sitrep_analyze import analyze

router = APIRouter(tags=["officer-sitrep"])


class SitrepIn(BaseModel):
    transcript: str = Field(min_length=8, max_length=8000)
    duration_s: float | None = Field(default=None, ge=0, le=180)
    rms_mean: float | None = None
    rms_var: float | None = None
    answers: list[dict] | None = None
    duty_date: str | None = None


@router.post("/me/sitreps")
def create_sitrep(
    body: SitrepIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("commander")),
):
    day = as_of()
    if body.duty_date:
        try:
            from datetime import date as date_cls

            day = date_cls.fromisoformat(body.duty_date[:10])
        except ValueError:
            day = as_of()
    result = analyze(
        body.transcript,
        rms_mean=body.rms_mean,
        rms_var=body.rms_var,
        answers=body.answers,
        use_llm=True,
    )
    row = DutySitrep(
        id=nid("sr"),
        user_id=user.id,
        duty_date=day,
        transcript=body.transcript.strip(),
        work_summary=result["work_summary"],
        work_bullets=result["work_bullets"],
        answers=body.answers,
        tone_label=result["tone_label"],
        mood_label=result["mood_label"],
        mood_score=result["mood_score"],
        wellness_summary=result["wellness_summary"],
        flags=result["flags"],
        duration_s=body.duration_s,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    write_audit(
        db,
        actor=user,
        action="app.own_sitrep",
        resource_type="duty_sitrep",
        resource_id=row.id,
        purpose="duty_log",
    )
    return _out(row, questions=result["questions"])


@router.get("/me/sitreps")
def list_sitreps(
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("commander")),
):
    rows = (
        db.query(DutySitrep)
        .filter(DutySitrep.user_id == user.id)
        .order_by(DutySitrep.duty_date.desc(), DutySitrep.created_at.desc())
        .limit(40)
        .all()
    )
    return {
        "self_scope": True,
        "as_of": as_of().isoformat(),
        "sitreps": [_out(r) for r in rows],
    }


def _out(row: DutySitrep, questions: list[str] | None = None) -> dict:
    payload = {
        "id": row.id,
        "duty_date": row.duty_date.isoformat(),
        "transcript": row.transcript,
        "work_summary": row.work_summary,
        "work_bullets": row.work_bullets,
        "tone_label": row.tone_label,
        "mood_label": row.mood_label,
        "mood_score": row.mood_score,
        "wellness_summary": row.wellness_summary,
        "flags": row.flags or [],
        "answers": row.answers,
        "duration_s": row.duration_s,
        "heuristic": "llm" not in (row.flags or []),
        "self_scope": True,
    }
    if questions is not None:
        payload["questions"] = questions
    return payload
