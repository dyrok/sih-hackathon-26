"""Idempotent upsert of the generated payload into the backend's tables.

Read-only dependency on ``backend/app/models.py``: this module imports those
SQLAlchemy models, it never modifies them. The backend package lives outside
this one, so it is put on ``sys.path`` lazily — importing ``data.writer_db``
without a database present must not explode, because ``--dry-run`` and the CSV
path do not need it.

**Idempotency is by natural key, not by row id.** Every table is matched on the
same natural key the backend's own ``UniqueConstraint`` / ingest de-duplication
uses, so re-running the generator — or running it after ``python -m app.seed``,
or before it — converges on one row per key instead of duplicating the arc. Row
ids are deterministic (``data.did``) for rows this generator creates, and rows
that already exist keep whatever id created them.

Nothing here computes signals or risk scores. Recompute is the backend's job:

    cd backend && .venv/bin/python -m app.seed        # users + recompute + score
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import Dataset

#: Rows per bulk statement.
CHUNK = 2000

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")
DEFAULT_DB_URL = "sqlite:///" + os.path.join(BACKEND_ROOT, "saarthi.db")


def default_db_url() -> str:
    """The backend's sqlite database, unless the backend env var overrides it."""
    return os.environ.get("SAARTHI_DATABASE_URL", DEFAULT_DB_URL)


def _import_backend():
    if BACKEND_ROOT not in sys.path:
        sys.path.insert(0, BACKEND_ROOT)
    from app import models  # noqa: WPS433 (deliberate lazy import)

    return models


# ---------------------------------------------------------------------------
# Column plans:  (model_attribute, payload_key, converter)
# ---------------------------------------------------------------------------

STR = "str"
DATE = "date"
DATETIME = "datetime"
BOOL = "bool"
INT = "int"
FLOAT = "float"
JSON = "json"


def _convert(value: Any, kind: str) -> Any:
    if value is None:
        return None
    if kind == DATE:
        return date.fromisoformat(value) if isinstance(value, str) else value
    if kind == DATETIME:
        return datetime.fromisoformat(value) if isinstance(value, str) else value
    if kind == BOOL:
        return bool(value)
    if kind == INT:
        return int(value)
    if kind == FLOAT:
        return float(value)
    return value


class TablePlan(object):
    """How one payload table maps onto one backend model."""

    def __init__(
        self,
        payload: str,
        model_name: str,
        pk: str,
        key: Sequence[str],
        columns: Sequence[Tuple[str, str, str]],
        id_prefix: Optional[str] = None,
    ) -> None:
        self.payload = payload
        self.model_name = model_name
        self.pk = pk
        self.key = tuple(key)
        self.columns = tuple(columns)
        self.id_prefix = id_prefix

    def mapping(self, row: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        for attr, payload_key, kind in self.columns:
            out[attr] = _convert(row.get(payload_key), kind)
        return out

    def key_of(self, row: Dict[str, Any]) -> Tuple[Any, ...]:
        return tuple(_norm(row.get(k)) for k in self.key)


def _norm(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


PLANS: Tuple[TablePlan, ...] = (
    TablePlan(
        "personnel", "IdentityMap", "personnel_id", ("personnel_id",),
        (
            ("personnel_id", "personnel_id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("unit_id", "unit_id", STR),
            ("rank", "rank", STR),
            ("age", "age", INT),
            ("legal_name", "legal_name", STR),
            ("skill_tags", "skill_tags", JSON),
        ),
    ),
    TablePlan(
        "leave", "HrLeaveRecord", "id", ("pseudonym_id", "applied_at", "leave_type"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("leave_type", "leave_type", STR),
            ("home_leave", "home_leave", BOOL),
            ("applied_at", "applied_at", DATE),
            ("sanctioned_from", "sanctioned_from", DATE),
            ("sanctioned_to", "sanctioned_to", DATE),
            ("cancelled_at", "cancelled_at", DATE),
            ("denial_reason", "denial_reason", STR),
            ("actual_return_date", "actual_return_date", DATE),
        ),
    ),
    TablePlan(
        "roster", "HrDutyRoster", "id", ("pseudonym_id", "duty_date"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("unit_id", "unit_id", STR),
            ("duty_date", "duty_date", DATE),
            ("shift_code", "shift_code", STR),
            ("rest_day", "rest_day", BOOL),
        ),
    ),
    TablePlan(
        "deployment", "HrDeployment", "id", ("pseudonym_id", "start_date", "posting_type"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("unit_id", "unit_id", STR),
            ("posting_type", "posting_type", STR),
            ("start_date", "start_date", DATE),
            ("end_date", "end_date", DATE),
            ("distance_km", "distance_km", FLOAT),
        ),
    ),
    TablePlan(
        "transfer", "HrTransfer", "id",
        ("pseudonym_id", "effective_date", "from_unit", "to_unit"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("from_unit", "from_unit", STR),
            ("to_unit", "to_unit", STR),
            ("effective_date", "effective_date", DATE),
            ("reason_code", "reason_code", STR),
        ),
    ),
    TablePlan(
        "incident", "HrIncident", "incident_id", ("incident_id",),
        (
            ("incident_id", "incident_id", STR),
            ("unit_id", "unit_id", STR),
            ("incident_type", "incident_type", STR),
            ("severity_band", "severity_band", STR),
            ("incident_date", "incident_date", DATE),
            ("exposure_window_days", "exposure_window_days", INT),
        ),
    ),
    TablePlan(
        "medical", "HrMedical", "id", ("pseudonym_id", "visit_date", "visit_type"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("visit_date", "visit_date", DATE),
            ("visit_type", "visit_type", STR),
            ("injury_flag", "injury_flag", BOOL),
        ),
    ),
    TablePlan(
        "career", "HrCareerState", "pseudonym_id", ("pseudonym_id",),
        (
            ("pseudonym_id", "pseudonym_id", STR),
            ("promotion_board_pending_months", "promotion_board_pending_months", FLOAT),
            ("inquiry_court_pending", "inquiry_court_pending", BOOL),
            ("inquiry_age_days", "inquiry_age_days", INT),
            ("denied_training_count_12m", "denied_training_count_12m", INT),
        ),
    ),
    TablePlan(
        "consent", "ConsentArtefact", "consent_id", ("principal_pseudonym", "bundle_id"),
        (
            ("consent_id", "consent_id", STR),
            ("principal_pseudonym", "principal_pseudonym", STR),
            ("bundle_id", "bundle_id", STR),
            ("purpose_string", "purpose_string", STR),
            ("data_categories", "data_categories", JSON),
            ("language", "language", STR),
            ("consent_version", "consent_version", STR),
            ("granted_at", "granted_at", DATETIME),
            ("withdrawn_at", "withdrawn_at", DATETIME),
            ("artefact_hash", "artefact_hash", STR),
        ),
    ),
    TablePlan(
        "checkin", "CheckIn", "id", ("pseudonym_id", "recorded_at"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("recorded_at", "recorded_at", DATE),
            ("mood_label", "mood_label", STR),
            ("mood_score", "mood_score", INT),
            ("sleep_hours", "sleep_hours", FLOAT),
            ("expires_at", "expires_at", DATE),
            ("purged", "purged", BOOL),
        ),
    ),
    TablePlan(
        "instrument", "InstrumentResult", "id", ("pseudonym_id", "instrument", "recorded_at"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("instrument", "instrument", STR),
            ("score", "score", INT),
            ("item_9", "item_9", INT),
            ("validity_fail", "validity_fail", BOOL),
            ("straight_lining", "straight_lining", BOOL),
            ("too_fast", "too_fast", BOOL),
            ("all_max", "all_max", BOOL),
            ("recorded_at", "recorded_at", DATE),
            ("expires_at", "expires_at", DATE),
            ("purged", "purged", BOOL),
        ),
    ),
    TablePlan(
        "passive", "PassiveFeature", "id", ("pseudonym_id", "recorded_at"),
        (
            ("id", "id", STR),
            ("pseudonym_id", "pseudonym_id", STR),
            ("recorded_at", "recorded_at", DATE),
            ("sleep_hours_proxy", "sleep_hours_proxy", FLOAT),
        ),
    ),
)


def _existing_ids(db, model, plan: TablePlan) -> Dict[Tuple[Any, ...], Any]:
    cols = [getattr(model, plan.pk)] + [getattr(model, c) for c in plan.key]
    out: Dict[Tuple[Any, ...], Any] = {}
    for row in db.query(*cols).all():
        out[tuple(_norm(v) for v in row[1:])] = row[0]
    return out


def _chunks(items: List[Any], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def write_db(ds: Dataset, db_url: Optional[str] = None) -> Dict[str, Dict[str, int]]:
    """Upsert the payload. Returns ``{table: {"inserted": n, "updated": n}}``."""
    models = _import_backend()
    from app.db import SessionLocal, configure_engine, init_db  # noqa: WPS433

    url = db_url or default_db_url()
    configure_engine(url)
    init_db()

    report: Dict[str, Dict[str, int]] = {}
    db = SessionLocal()
    try:
        for plan in PLANS:
            rows = ds.table(plan.payload)
            model = getattr(models, plan.model_name)
            existing = _existing_ids(db, model, plan)
            inserts: List[Dict[str, Any]] = []
            updates: List[Dict[str, Any]] = []
            seen = set()
            for row in rows:
                key = plan.key_of(row)
                if key in seen:
                    continue                             # payload-level duplicate
                seen.add(key)
                mapping = plan.mapping(row)
                if key in existing:
                    mapping[plan.pk] = existing[key]
                    updates.append(mapping)
                else:
                    inserts.append(mapping)
            for chunk in _chunks(inserts, CHUNK):
                db.bulk_insert_mappings(model, chunk)
            for chunk in _chunks(updates, CHUNK):
                db.bulk_update_mappings(model, chunk)
            db.flush()
            report[plan.payload] = {"inserted": len(inserts), "updated": len(updates)}
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return report
