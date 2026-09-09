"""Caseload scoping (ABAC) shared by every individual-data route.

F06 states that curiosity browsing is *structurally* impossible because a case
exists only when the engine raises one. That is only true if the individual
routes check the caseload, not just the role — otherwise the queue is scoped and
the detail is not, which is the classic IDOR shape.

One helper, used by /risk, /signals and every /interventions item route, so the
rule cannot drift between them.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi import HTTPException

from .audit import write_deny
from .models import ResponseCase, TriageEntry, User


def _cases_for(db: Session, pseudonym_id: str) -> list[ResponseCase]:
    return (
        db.query(ResponseCase)
        .filter(ResponseCase.pseudonym_id == pseudonym_id)
        .order_by(ResponseCase.opened_at.desc())
        .all()
    )


def _assignee(db: Session, case: ResponseCase) -> str | None:
    tri = db.query(TriageEntry).filter(TriageEntry.case_id == case.id).one_or_none()
    return tri.assigned_counsellor_id if tri else None


def _deny(db: Session, user: User, *, resource_type: str, resource_id: str, reason: str) -> None:
    write_deny(
        db,
        actor=user,
        action="scope.deny",
        resource_type=resource_type,
        resource_id=resource_id,
        subject_pseudonym_id=resource_id,
        denied=True,
        reason=reason,
    )
    raise HTTPException(403, "no case assigns this subject to you (%s)" % reason)


def may_read_subject(db: Session, user: User, pseudonym_id: str) -> bool:
    """True when this principal has a live reason to see this person's data.

    counsellor       — a case exists for the subject and is assigned to them, or
                       is still unassigned (the shared pool a counsellor may pick
                       up). An unassigned case is a real work item, not a
                       browsing hole: it exists only because the engine raised it.
    welfare_officer  — a case exists and its unit is one they are assigned to.
                       An empty assignment list means *no* units, never all of
                       them; "unset" must never widen access.
    """
    cases = _cases_for(db, pseudonym_id)
    if not cases:
        return False
    if user.role == "counsellor":
        for case in cases:
            assignee = _assignee(db, case)
            if assignee in (None, user.id):
                return True
        return False
    if user.role == "welfare_officer":
        units = user.assigned_units or []
        if not units:
            return False
        return any(case.unit_id in units for case in cases)
    return False


def assert_subject_scope(db: Session, user: User, pseudonym_id: str, *, resource_type: str) -> None:
    if may_read_subject(db, user, pseudonym_id):
        return
    _deny(
        db,
        user,
        resource_type=resource_type,
        resource_id=pseudonym_id,
        reason="subject is not on this principal's caseload",
    )


def assert_case_scope(db: Session, user: User, case: ResponseCase) -> None:
    """Write-side guard: acting on a case requires it to be *yours*.

    Stricter than the read guard on purpose — reading an unassigned case is
    triage, but closing one, recording an outcome, or filing a Tele-MANAS
    referral against it is an intervention on someone else's work.
    """
    if user.role == "counsellor":
        assignee = _assignee(db, case)
        if assignee not in (None, user.id):
            _deny(
                db,
                user,
                resource_type="response_case",
                resource_id=case.id,
                reason="case is assigned to another counsellor",
            )
        return
    if user.role == "welfare_officer":
        units = user.assigned_units or []
        if not units or (case.unit_id is not None and case.unit_id not in units):
            _deny(
                db,
                user,
                resource_type="response_case",
                resource_id=case.id,
                reason="case is outside your assigned units",
            )
        return
    _deny(
        db,
        user,
        resource_type="response_case",
        resource_id=case.id,
        reason="role cannot act on a case",
    )
