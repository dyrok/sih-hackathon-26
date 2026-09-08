from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..config import get_settings
from ..ids import nid
from ..models import (
    HrCareerState,
    HrDeployment,
    HrDutyRoster,
    HrIncident,
    HrLeaveRecord,
    HrMedical,
    HrTransfer,
    IdentityMap,
    SignalGroupFlag,
    SignalSnapshot,
)
from .calculator import compute_person_signals
from .domain import events as T
from .types import CareerRow, DeploymentRow, DutyRow, LeaveRow, MedicalRow, TransferRow


def _leave_rows(db: Session, pid: str) -> list[LeaveRow]:
    rows = db.query(HrLeaveRecord).filter(HrLeaveRecord.pseudonym_id == pid).all()
    return [
        LeaveRow(
            leave_type=r.leave_type,
            home_leave=r.home_leave,
            applied_at=r.applied_at,
            sanctioned_from=r.sanctioned_from,
            sanctioned_to=r.sanctioned_to,
            cancelled_at=r.cancelled_at,
            denial_reason=r.denial_reason,
            actual_return_date=r.actual_return_date,
        )
        for r in rows
    ]


def _duty_rows(db: Session, pid: str) -> list[DutyRow]:
    rows = db.query(HrDutyRoster).filter(HrDutyRoster.pseudonym_id == pid).all()
    return [
        DutyRow(duty_date=r.duty_date, shift_code=r.shift_code, rest_day=r.rest_day, unit_id=r.unit_id)
        for r in rows
    ]


def _dep_rows(db: Session, pid: str) -> list[DeploymentRow]:
    rows = db.query(HrDeployment).filter(HrDeployment.pseudonym_id == pid).all()
    return [
        DeploymentRow(
            posting_type=r.posting_type,
            start_date=r.start_date,
            end_date=r.end_date,
            distance_km=r.distance_km,
            unit_id=r.unit_id,
        )
        for r in rows
    ]


def _xfer_rows(db: Session, pid: str) -> list[TransferRow]:
    rows = db.query(HrTransfer).filter(HrTransfer.pseudonym_id == pid).all()
    return [
        TransferRow(
            from_unit=r.from_unit,
            to_unit=r.to_unit,
            effective_date=r.effective_date,
            reason_code=r.reason_code,
        )
        for r in rows
    ]


def _med_rows(db: Session, pid: str) -> list[MedicalRow]:
    rows = db.query(HrMedical).filter(HrMedical.pseudonym_id == pid).all()
    return [
        MedicalRow(visit_date=r.visit_date, visit_type=r.visit_type, injury_flag=r.injury_flag)
        for r in rows
    ]


def _career(db: Session, pid: str) -> CareerRow | None:
    r = db.get(HrCareerState, pid)
    if r is None:
        return None
    return CareerRow(
        promotion_board_pending_months=r.promotion_board_pending_months,
        inquiry_court_pending=r.inquiry_court_pending,
        inquiry_age_days=r.inquiry_age_days,
        denied_training_count_12m=r.denied_training_count_12m,
    )


def upsert_signals(db: Session, pseudonym_id: str, as_of: date, source_batch: str | None = None) -> dict[str, float | None]:
    values = compute_person_signals(
        as_of=as_of,
        leave=_leave_rows(db, pseudonym_id),
        duty=_duty_rows(db, pseudonym_id),
        deployments=_dep_rows(db, pseudonym_id),
        transfers=_xfer_rows(db, pseudonym_id),
        medical=_med_rows(db, pseudonym_id),
        career=_career(db, pseudonym_id),
    )
    window_start = as_of - timedelta(days=89)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    settings = get_settings()
    for key, value in values.items():
        existing = (
            db.query(SignalSnapshot)
            .filter(
                SignalSnapshot.pseudonym_id == pseudonym_id,
                SignalSnapshot.signal_key == key,
                SignalSnapshot.window_end == as_of,
            )
            .one_or_none()
        )
        if existing:
            existing.value = value
            existing.computed_at = now
            existing.engine_version = settings.engine_version
            existing.source_batch = source_batch
        else:
            db.add(
                SignalSnapshot(
                    id=nid("sig"),
                    pseudonym_id=pseudonym_id,
                    signal_key=key,
                    value=value,
                    window_start=window_start,
                    window_end=as_of,
                    computed_at=now,
                    engine_version=settings.engine_version,
                    source_batch=source_batch,
                )
            )
    db.flush()
    return values


def recompute_group_flags(db: Session, as_of: date) -> list[str]:
    """Returns unit_ids with active exposure flags. Flags are unit-scoped (FR-08)."""
    dirty_units: list[str] = []
    incidents = db.query(HrIncident).all()
    for inc in incidents:
        exposed = T.unit_incident_exposure(inc.incident_date, inc.exposure_window_days, as_of)
        until = inc.incident_date + timedelta(days=inc.exposure_window_days)
        existing = (
            db.query(SignalGroupFlag)
            .filter(
                SignalGroupFlag.unit_id == inc.unit_id,
                SignalGroupFlag.signal_key == "unit_incident_exposure",
                SignalGroupFlag.incident_id == inc.incident_id,
            )
            .one_or_none()
        )
        if existing:
            existing.value = exposed
            existing.valid_from = inc.incident_date
            existing.valid_until = until
        else:
            db.add(
                SignalGroupFlag(
                    id=nid("gflg"),
                    unit_id=inc.unit_id,
                    signal_key="unit_incident_exposure",
                    value=exposed,
                    incident_id=inc.incident_id,
                    valid_from=inc.incident_date,
                    valid_until=until,
                )
            )
        days_row = (
            db.query(SignalGroupFlag)
            .filter(
                SignalGroupFlag.unit_id == inc.unit_id,
                SignalGroupFlag.signal_key == "days_since_unit_incident",
                SignalGroupFlag.incident_id == inc.incident_id,
            )
            .one_or_none()
        )
        days_val = T.days_since_unit_incident(inc.incident_date, as_of)
        if days_row:
            days_row.value = days_val
        else:
            db.add(
                SignalGroupFlag(
                    id=nid("gflg"),
                    unit_id=inc.unit_id,
                    signal_key="days_since_unit_incident",
                    value=days_val,
                    incident_id=inc.incident_id,
                    valid_from=inc.incident_date,
                    valid_until=until,
                )
            )
        if exposed:
            dirty_units.append(inc.unit_id)
    db.flush()
    return dirty_units


def dirty_pseudonyms(db: Session, extra: list[str] | None = None) -> list[str]:
    ids = {row.pseudonym_id for row in db.query(IdentityMap).all()}
    if extra:
        ids.update(extra)
    return sorted(ids)


def recompute_all(db: Session, as_of: date, source_batch: str | None = None, only: list[str] | None = None) -> list[str]:
    recompute_group_flags(db, as_of)
    people = only or [r.pseudonym_id for r in db.query(IdentityMap).all()]
    for pid in people:
        upsert_signals(db, pid, as_of, source_batch=source_batch)
    return people
