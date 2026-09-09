from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit, write_deny
from ...config import get_settings
from ...clock import as_of
from ...db import get_db
from ...firewall import forbid_commander
from ...ingest.pipeline import ingest_rows, parse_csv
from ...ingest.schemas import DATASETS
from ...models import IngestBatch, QuarantineRow, User
from ...security import require_roles
from ...signals.snapshot import recompute_all

router = APIRouter(tags=["ingest"])


class JsonBatch(BaseModel):
    batch_id: str
    rows: list[dict]


@router.post("/ingest/hr/csv")
def ingest_csv(
    dataset: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("hr_ingest", "admin")),
):
    forbid_commander(user, db=db, resource_type="ingest")
    if dataset not in DATASETS:
        raise HTTPException(400, f"unknown dataset {dataset}")
    # Bounded read: an unbounded upload on a laptop-class demo box is a
    # one-request denial of service (TC-458).
    limit = get_settings().max_ingest_bytes
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, "upload exceeds %d bytes" % limit)
    rows = parse_csv(content)
    batch_id = f"csv-{dataset}-{file.filename}"
    result = ingest_rows(
        db, dataset=dataset, batch_id=batch_id, rows=rows, source="csv",
        submitted_by_user_id=user.id,
    )
    write_audit(
        db,
        actor=user,
        action="ingest.csv",
        resource_type="ingest_batch",
        resource_id=batch_id,
        payload={"dataset": dataset, **{k: result[k] for k in ("rows_in", "rows_written", "rows_quarantined")}},
    )
    return result


@router.post("/ingest/hr/{dataset}")
def ingest_json(
    dataset: str,
    body: JsonBatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("hr_ingest", "admin")),
):
    forbid_commander(user, db=db, resource_type="ingest")
    if dataset not in DATASETS:
        raise HTTPException(400, f"unknown dataset {dataset}")
    result = ingest_rows(
        db, dataset=dataset, batch_id=body.batch_id, rows=body.rows, source="api",
        submitted_by_user_id=user.id,
    )
    write_audit(
        db,
        actor=user,
        action="ingest.json",
        resource_type="ingest_batch",
        resource_id=body.batch_id,
        payload={"dataset": dataset, "rows_in": result["rows_in"]},
    )
    return result


@router.get("/ingest/hr/batches/{batch_id}/quarantine")
def quarantine_report(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("hr_ingest", "admin", "auditor")),
):
    """A rejected row is still an HR row about a person.

    Batch ids are chosen by the caller and are therefore guessable, so the
    report was addressable by any ingest account for anyone else's batch
    (TC-424). Three things fix it: the batch is scoped to its submitter, the
    payload is withheld from roles with no content grant, and every read is
    audited.
    """
    batch = db.get(IngestBatch, batch_id)
    if batch is None:
        raise HTTPException(404, "batch not found")
    if user.role == "hr_ingest" and batch.submitted_by_user_id not in (None, user.id):
        write_deny(
            db,
            actor=user,
            action="ingest.quarantine.deny",
            resource_type="ingest_batch",
            resource_id=batch_id,
            reason="batch belongs to another ingest principal",
        )
        raise HTTPException(403, "batch belongs to another ingest principal")

    # RBAC matrix: admin operates pipelines with no content access, and the
    # auditor is content-blind. Only the submitting service account — which
    # supplied these rows in the first place — sees them back.
    include_payload = user.role == "hr_ingest"
    rows = db.query(QuarantineRow).filter(QuarantineRow.batch_id == batch_id).all()
    write_audit(
        db,
        actor=user,
        action="ingest.quarantine.read",
        resource_type="ingest_batch",
        resource_id=batch_id,
        purpose="data_quality",
        payload={"rows": len(rows), "payload_included": include_payload},
    )
    return {
        "batch_id": batch_id,
        "dataset": batch.dataset,
        "status": batch.status,
        "payload_included": include_payload,
        "rows": [
            {
                "index": r.row_index,
                "reason": r.reason,
                **({"payload": r.payload} if include_payload else {}),
            }
            for r in rows
        ],
    }


@router.post("/signals/recompute")
def recompute(
    body: dict | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "hr_ingest")),
):
    forbid_commander(user, db=db, resource_type="signals")
    body = body or {}
    only = body.get("pseudonyms")
    people = recompute_all(db, as_of(), only=only)
    write_audit(db, actor=user, action="signals.recompute", resource_type="signals", payload={"n": len(people)})
    return {"recomputed": len(people)}
