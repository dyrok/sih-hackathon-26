from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..clock import as_of
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
    IngestBatch,
    QuarantineRow,
)
from ..signals.snapshot import recompute_all
from .schemas import SCHEMA_BY_DATASET

_LEAVE_TYPES = {"home_leave", "casual", "earned", "medical", "other"}
_SHIFTS = {"day", "evening", "night", "pt_absent"}


def _row_hash(rows: list[dict]) -> str:
    blob = repr(sorted((k, str(v)) for row in rows for k, v in sorted(row.items()))).encode()
    return hashlib.sha256(blob).hexdigest()


def _pseudonym(db: Session, personnel_id: str) -> str | None:
    ident = db.get(IdentityMap, personnel_id)
    return ident.pseudonym_id if ident else None


def parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for raw in reader:
        rows.append({(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items()})
    return rows


def ingest_rows(
    db: Session,
    *,
    dataset: str,
    batch_id: str,
    rows: list[dict],
    source: str,
    recompute: bool = True,
    submitted_by_user_id: str | None = None,
) -> dict[str, Any]:
    if dataset not in SCHEMA_BY_DATASET:
        raise ValueError(f"unknown dataset {dataset}")
    existing = db.get(IngestBatch, batch_id)
    if existing and existing.status == "committed":
        return {
            "batch_id": batch_id,
            "rows_in": existing.rows_in,
            "rows_written": existing.rows_written,
            "rows_quarantined": existing.rows_quarantined,
            "status": "duplicate_noop",
            "quarantine_report_url": f"/ingest/hr/batches/{batch_id}/quarantine",
        }

    schema = SCHEMA_BY_DATASET[dataset]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    batch = existing or IngestBatch(
        batch_id=batch_id,
        source=source,
        dataset=dataset,
        rows_in=len(rows),
        rows_written=0,
        rows_quarantined=0,
        status="staging",
        received_at=now,
        batch_hash=_row_hash(rows),
        submitted_by_user_id=submitted_by_user_id,
    )
    if existing is None:
        db.add(batch)
        db.flush()
    else:
        batch.rows_in = len(rows)
        batch.batch_hash = _row_hash(rows)
        if batch.submitted_by_user_id is None:
            batch.submitted_by_user_id = submitted_by_user_id

    written = 0
    quarantined = 0
    dirty: list[str] = []

    for idx, raw in enumerate(rows):
        try:
            model = schema.model_validate(raw)
        except (ValidationError, ValueError) as exc:
            db.add(
                QuarantineRow(
                    id=nid("q"),
                    batch_id=batch_id,
                    dataset=dataset,
                    row_index=idx,
                    payload=raw,
                    reason=str(exc)[:500],
                )
            )
            quarantined += 1
            continue

        data = model.model_dump()
        personnel_id = data.get("personnel_id")
        pid = None
        if dataset != "incident":
            pid = _pseudonym(db, personnel_id)
            if pid is None:
                db.add(
                    QuarantineRow(
                        id=nid("q"),
                        batch_id=batch_id,
                        dataset=dataset,
                        row_index=idx,
                        payload=raw,
                        reason="unknown personnel_id",
                    )
                )
                quarantined += 1
                continue
            dirty.append(pid)

        if _is_duplicate(db, dataset, pid, data):
            db.add(
                QuarantineRow(
                    id=nid("q"),
                    batch_id=batch_id,
                    dataset=dataset,
                    row_index=idx,
                    payload=raw,
                    reason="duplicate natural key",
                )
            )
            quarantined += 1
            continue
        _persist(db, dataset, pid, data, batch_id)
        written += 1

    batch.rows_written = written
    batch.rows_quarantined = quarantined
    batch.status = "committed"
    db.flush()

    if recompute:
        recompute_all(db, as_of(), source_batch=batch_id, only=sorted(set(dirty)) or None)

    return {
        "batch_id": batch_id,
        "rows_in": len(rows),
        "rows_written": written,
        "rows_quarantined": quarantined,
        "status": "committed",
        "quarantine_report_url": f"/ingest/hr/batches/{batch_id}/quarantine",
    }


def _is_duplicate(db: Session, dataset: str, pid: str | None, data: dict) -> bool:
    if dataset == "leave":
        return (
            db.query(HrLeaveRecord)
            .filter(
                HrLeaveRecord.pseudonym_id == pid,
                HrLeaveRecord.applied_at == data["applied_at"],
                HrLeaveRecord.leave_type == data["leave_type"],
            )
            .first()
            is not None
        )
    if dataset == "roster":
        return (
            db.query(HrDutyRoster)
            .filter(HrDutyRoster.pseudonym_id == pid, HrDutyRoster.duty_date == data["duty_date"])
            .first()
            is not None
        )
    if dataset == "deployment":
        return (
            db.query(HrDeployment)
            .filter(
                HrDeployment.pseudonym_id == pid,
                HrDeployment.start_date == data["start_date"],
                HrDeployment.posting_type == data["posting_type"],
            )
            .first()
            is not None
        )
    if dataset == "transfer":
        return (
            db.query(HrTransfer)
            .filter(
                HrTransfer.pseudonym_id == pid,
                HrTransfer.effective_date == data["effective_date"],
                HrTransfer.from_unit == data["from_unit"],
                HrTransfer.to_unit == data["to_unit"],
            )
            .first()
            is not None
        )
    if dataset == "incident":
        return False  # upserted in _persist
    if dataset == "medical":
        return (
            db.query(HrMedical)
            .filter(
                HrMedical.pseudonym_id == pid,
                HrMedical.visit_date == data["visit_date"],
                HrMedical.visit_type == data["visit_type"],
            )
            .first()
            is not None
        )
    return False


def _persist(db: Session, dataset: str, pid: str | None, data: dict, batch_id: str) -> None:
    if dataset == "leave":
        db.add(
            HrLeaveRecord(
                id=nid("lv"),
                pseudonym_id=pid,
                leave_type=data["leave_type"],
                home_leave=data["home_leave"] or data["leave_type"] == "home_leave",
                applied_at=data["applied_at"],
                sanctioned_from=data["sanctioned_from"],
                sanctioned_to=data["sanctioned_to"],
                cancelled_at=data["cancelled_at"],
                denial_reason=data["denial_reason"],
                actual_return_date=data["actual_return_date"],
                batch_id=batch_id,
            )
        )
    elif dataset == "roster":
        db.add(
            HrDutyRoster(
                id=nid("dt"),
                pseudonym_id=pid,
                unit_id=data["unit_id"],
                duty_date=data["duty_date"],
                shift_code=data["shift_code"],
                rest_day=data["rest_day"],
                batch_id=batch_id,
            )
        )
    elif dataset == "deployment":
        db.add(
            HrDeployment(
                id=nid("dp"),
                pseudonym_id=pid,
                unit_id=data["unit_id"],
                posting_type=data["posting_type"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                distance_km=data["distance_km"],
                batch_id=batch_id,
            )
        )
    elif dataset == "transfer":
        db.add(
            HrTransfer(
                id=nid("xf"),
                pseudonym_id=pid,
                from_unit=data["from_unit"],
                to_unit=data["to_unit"],
                effective_date=data["effective_date"],
                reason_code=data["reason_code"],
                batch_id=batch_id,
            )
        )
    elif dataset == "incident":
        existing = db.get(HrIncident, data["incident_id"])
        if existing:
            existing.unit_id = data["unit_id"]
            existing.incident_type = data["incident_type"]
            existing.severity_band = data["severity_band"]
            existing.incident_date = data["incident_date"]
            existing.exposure_window_days = data["exposure_window_days"]
            existing.batch_id = batch_id
        else:
            db.add(
                HrIncident(
                    incident_id=data["incident_id"],
                    unit_id=data["unit_id"],
                    incident_type=data["incident_type"],
                    severity_band=data["severity_band"],
                    incident_date=data["incident_date"],
                    exposure_window_days=data["exposure_window_days"],
                    batch_id=batch_id,
                )
            )
    elif dataset == "medical":
        db.add(
            HrMedical(
                id=nid("md"),
                pseudonym_id=pid,
                visit_date=data["visit_date"],
                visit_type=data["visit_type"],
                injury_flag=data["injury_flag"],
                batch_id=batch_id,
            )
        )
    elif dataset == "career":
        row = db.get(HrCareerState, pid)
        if row:
            row.promotion_board_pending_months = data["promotion_board_pending_months"]
            row.inquiry_court_pending = data["inquiry_court_pending"]
            row.inquiry_age_days = data["inquiry_age_days"]
            row.denied_training_count_12m = data["denied_training_count_12m"]
        else:
            db.add(
                HrCareerState(
                    pseudonym_id=pid,
                    promotion_board_pending_months=data["promotion_board_pending_months"],
                    inquiry_court_pending=data["inquiry_court_pending"],
                    inquiry_age_days=data["inquiry_age_days"],
                    denied_training_count_12m=data["denied_training_count_12m"],
                )
            )
    db.flush()
