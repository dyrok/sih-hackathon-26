from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of
from ...db import get_db
from ...firewall import forbid_commander
from ...ingest.pipeline import ingest_rows, parse_csv
from ...ingest.schemas import DATASETS
from ...models import QuarantineRow, User
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
    content = file.file.read()
    rows = parse_csv(content)
    batch_id = f"csv-{dataset}-{file.filename}"
    result = ingest_rows(db, dataset=dataset, batch_id=batch_id, rows=rows, source="csv")
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
    result = ingest_rows(db, dataset=dataset, batch_id=body.batch_id, rows=body.rows, source="api")
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
    rows = db.query(QuarantineRow).filter(QuarantineRow.batch_id == batch_id).all()
    return {
        "batch_id": batch_id,
        "rows": [{"index": r.row_index, "reason": r.reason, "payload": r.payload} for r in rows],
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
