"""Jawan self-scope surface (F02 screens 1, 4, 5, 6, 9 · F03 screens 2-4).

Every handler resolves the subject from the token. No route in this module
accepts a personnel id, a pseudonym, or any other subject selector — one token
can only ever address its own rows (F02 privacy note 4).
"""

from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...audit import write_audit
from ...clock import as_of, clamp_capture_date
from ...config import get_settings
from ...consent import active_consent
from ...db import get_db
from ...ids import nid
from ...models import (
    CheckIn,
    ConsentArtefact,
    HrDutyRoster,
    HrLeaveRecord,
    IdentityMap,
    InstrumentResult,
    Notification,
    PassiveFeature,
    SyncReceipt,
    UnitPulseRating,
    User,
    VoiceFeature,
)
from ...security import get_current_user, require_roles

router = APIRouter(tags=["jawan-self-service"])

#: F02 consent model — unbundled scopes. Withdrawal is the same tap depth as
#: granting and is silent to command (FR-17).
BUNDLES: dict[str, dict[str, Any]] = {
    "checkin": {
        "label_key": "consent.scope.checkin",
        "purpose_key": "consent.purpose.checkin",
        "data_categories": ["mood", "stress_slider", "free_text", "sleep_hours"],
        "retention_days": 90,
    },
    "instruments": {
        "label_key": "consent.scope.instrument",
        "purpose_key": "consent.purpose.instrument",
        "data_categories": ["phq9", "gad7", "pss10", "isi", "validity_items"],
        "retention_days": 90,
    },
    "voice": {
        "label_key": "consent.scope.voice",
        "purpose_key": "consent.purpose.voice",
        "data_categories": ["prosody_feature_vector"],
        "retention_days": 90,
    },
    "passive": {
        "label_key": "consent.scope.passive",
        "purpose_key": "consent.purpose.passive",
        "data_categories": ["sleep_proxy"],
        "retention_days": 90,
    },
    "unit_pulse": {
        "label_key": "consent.scope.pulse",
        "purpose_key": "consent.purpose.pulse",
        "data_categories": ["unit_climate_rating"],
        "retention_days": 365,
    },
    "buddy": {
        "label_key": "consent.scope.buddy",
        "purpose_key": "consent.purpose.buddy",
        "data_categories": ["coarse_buddy_state"],
        "retention_days": 365,
    },
}

#: F03 — the ONLY fields that may cross the wire from a voice check-in.
VOICE_SCHEMA_VERSIONS = {"v1"}

INSTRUMENTS = ("PHQ-9", "GAD-7", "PSS-10", "ISI")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _day(raw: str | None) -> date_cls:
    """Clamped capture date — a queued row from a long-offline device is kept,
    but a client cannot post a future date to escape the 90-day TTL (TC-455)."""
    return clamp_capture_date(raw, as_of())


def _self_pseudonym(db: Session, user: User) -> str:
    """Every principal gets a self-scope pseudonym on first write.

    F07 screen 6: a commander takes the same 10-second check-in under their own
    token (officer-first rollout, ADR-0004). Because there is no IdentityMap row
    for a minted self-pseudonym, that check-in never enters a unit aggregate and
    is invisible to everyone including themselves in any other surface.
    """
    if user.pseudonym_id:
        return user.pseudonym_id
    user.pseudonym_id = "ps_self_%s" % user.id.replace("-", "")[:16]
    db.flush()
    return user.pseudonym_id


# ---------------------------------------------------------------------------
# Consent panel (F02 screen 5)
# ---------------------------------------------------------------------------


@router.get("/app/consent")
def my_consent(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    rows = (
        db.query(ConsentArtefact)
        .filter(ConsentArtefact.principal_pseudonym == user.pseudonym_id)
        .order_by(ConsentArtefact.granted_at.desc())
        .all()
    )
    latest: dict[str, ConsentArtefact] = {}
    for r in rows:
        if r.bundle_id not in latest:
            latest[r.bundle_id] = r
    bundles = []
    for bundle_id, spec in BUNDLES.items():
        row = latest.get(bundle_id)
        granted = row is not None and row.withdrawn_at is None
        bundles.append(
            {
                "bundle_id": bundle_id,
                "granted": granted,
                "granted_at": row.granted_at.isoformat() if row and granted else None,
                "withdrawn_at": (
                    row.withdrawn_at.isoformat() if row and row.withdrawn_at else None
                ),
                "consent_version": row.consent_version if row else None,
                **spec,
            }
        )
    return {
        "title_key": "consent.sheet.title",
        "withdraw_key": "consent.withdraw.action",
        "confirm_key": "consent.withdraw.confirm",
        "silent_key": "consent.withdraw.silent",
        "bundles": bundles,
    }


@router.post("/app/consent/withdraw/{bundle_id}")
def withdraw_bundle(
    bundle_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    """Per-scope silent withdrawal (FR-17). Writes only to the consent store and
    the audit log — no command-visible table has a read path from either."""
    if bundle_id not in BUNDLES:
        raise HTTPException(404, "unknown consent bundle")
    rows = (
        db.query(ConsentArtefact)
        .filter(
            ConsentArtefact.principal_pseudonym == user.pseudonym_id,
            ConsentArtefact.bundle_id == bundle_id,
            ConsentArtefact.withdrawn_at.is_(None),
        )
        .all()
    )
    now = _now()
    for r in rows:
        r.withdrawn_at = now
    db.flush()
    write_audit(
        db,
        actor=user,
        action="consent.withdraw",
        resource_type="consent_artefact",
        resource_id=bundle_id,
        subject_pseudonym_id=user.pseudonym_id,
        purpose="principal_rights",
        reason="silent_withdrawal",
    )
    return {"bundle_id": bundle_id, "withdrawn": len(rows), "command_visible": False}


# ---------------------------------------------------------------------------
# Offline outbox drain (ADR-0005 · TC-601..605)
# ---------------------------------------------------------------------------


class SyncItem(BaseModel):
    table: str
    client_uuid: str
    captured_at: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncBatch(BaseModel):
    items: list[SyncItem]


def _apply_checkin(db: Session, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    day = _day(payload.get("recorded_at"))
    existing = (
        db.query(CheckIn)
        .filter(CheckIn.pseudonym_id == pid, CheckIn.recorded_at == day, CheckIn.purged.is_(False))
        .first()
    )
    if existing:
        # Conflict policy (design-client-apps §2): a re-submitted check-in for
        # the same local day keeps the earliest capture. Never a silent
        # overwrite, never a duplicate row.
        return {"status": "duplicate_day", "id": existing.id}
    row = CheckIn(
        id=nid("ck"),
        pseudonym_id=pid,
        recorded_at=day,
        mood_label=payload.get("mood_label"),
        mood_score=payload.get("mood_score"),
        sleep_hours=payload.get("sleep_hours"),
        expires_at=day + timedelta(days=get_settings().raw_ttl_days),
        purged=False,
    )
    db.add(row)
    db.flush()
    return {"status": "written", "id": row.id}


def _apply_instrument(db: Session, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    instrument = str(payload.get("instrument") or "")
    if instrument not in INSTRUMENTS:
        raise HTTPException(400, "instrument must be one of %s" % ", ".join(INSTRUMENTS))
    day = _day(payload.get("recorded_at"))
    month_start = day.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    existing = (
        db.query(InstrumentResult)
        .filter(
            InstrumentResult.pseudonym_id == pid,
            InstrumentResult.instrument == instrument,
            InstrumentResult.recorded_at >= month_start,
            InstrumentResult.recorded_at < next_month,
            InstrumentResult.purged.is_(False),
        )
        .first()
    )
    if existing:
        # One instrument per month, enforced server-side (F02 API surface).
        return {"status": "already_this_month", "id": existing.id}
    row = InstrumentResult(
        id=nid("in"),
        pseudonym_id=pid,
        instrument=instrument,
        score=int(payload.get("score") or 0),
        item_9=payload.get("item_9"),
        validity_fail=bool(payload.get("validity_fail")),
        straight_lining=bool(payload.get("straight_lining")),
        too_fast=bool(payload.get("too_fast")),
        all_max=bool(payload.get("all_max")),
        recorded_at=day,
        expires_at=day + timedelta(days=get_settings().raw_ttl_days),
        purged=False,
    )
    db.add(row)
    db.flush()
    return {"status": "written", "id": row.id}


def _apply_passive(db: Session, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    day = _day(payload.get("recorded_at"))
    existing = (
        db.query(PassiveFeature)
        .filter(PassiveFeature.pseudonym_id == pid, PassiveFeature.recorded_at == day)
        .first()
    )
    if existing:
        return {"status": "duplicate_day", "id": existing.id}
    row = PassiveFeature(
        id=nid("pf"),
        pseudonym_id=pid,
        sleep_hours_proxy=payload.get("sleep_hours_proxy"),
        recorded_at=day,
    )
    db.add(row)
    db.flush()
    return {"status": "written", "id": row.id, "raw_audio": False}


def _apply_voice(db: Session, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    schema_version = str(payload.get("schema_version") or "")
    if schema_version not in VOICE_SCHEMA_VERSIONS:
        # Unknown versions are rejected, never silently accepted (F03).
        raise HTTPException(400, "unknown voice schema_version %r" % schema_version)
    forbidden = {"audio", "audio_b64", "waveform", "transcript", "speaker_embedding", "voice_print"}
    present = forbidden & set(payload)
    if present:
        raise HTTPException(
            400, "payload carries identity/content fields that may never leave the device: %s" % sorted(present)
        )
    duration = float(payload.get("duration_s") or 0)
    if not 5.0 <= duration <= 30.0:
        raise HTTPException(400, "duration_s must be between 5 and 30 seconds")
    day = _day(payload.get("recorded_at"))
    row = VoiceFeature(
        id=nid("vf"),
        pseudonym_id=pid,
        recorded_at=day,
        f0_mean=payload.get("f0_mean"),
        f0_sd=payload.get("f0_sd"),
        speech_rate=payload.get("speech_rate"),
        pause_count=payload.get("pause_count"),
        pause_total=payload.get("pause_total"),
        voiced_ratio=payload.get("voiced_ratio"),
        loudness_var=payload.get("loudness_var"),
        jitter=payload.get("jitter"),
        shimmer=payload.get("shimmer"),
        duration_s=duration,
        model_version=str(payload.get("model_version") or "web-prosody-v1"),
        schema_version=schema_version,
        expires_at=day + timedelta(days=get_settings().raw_ttl_days),
        purged=False,
    )
    db.add(row)
    db.flush()
    return {"status": "written", "id": row.id, "raw_audio": False}


def _apply_pulse(db: Session, pid: str, payload: dict[str, Any]) -> dict[str, Any]:
    from .pulse import FACETS, period_of

    facet = str(payload.get("facet") or "")
    if facet not in FACETS:
        raise HTTPException(400, "facet must be one of %s" % ", ".join(FACETS))
    rating = int(payload.get("rating") or 0)
    if not 1 <= rating <= 5:
        raise HTTPException(400, "rating must be 1..5")
    day = _day(payload.get("recorded_at"))
    period = str(payload.get("period") or period_of(day))
    ident = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == pid).one_or_none()
    if ident is None:
        raise HTTPException(409, "no unit on file for this principal")
    existing = (
        db.query(UnitPulseRating)
        .filter(
            UnitPulseRating.pseudonym_id == pid,
            UnitPulseRating.period == period,
            UnitPulseRating.facet == facet,
        )
        .one_or_none()
    )
    if existing:
        existing.rating = rating
        existing.recorded_at = day
        return {"status": "replaced", "id": existing.id}
    row = UnitPulseRating(
        id=nid("pl"),
        pseudonym_id=pid,
        unit_id=ident.unit_id,
        period=period,
        facet=facet,
        rating=rating,
        recorded_at=day,
    )
    db.add(row)
    db.flush()
    return {"status": "written", "id": row.id}


def _apply_consent(db: Session, pid: str, payload: dict[str, Any], user: User) -> dict[str, Any]:
    bundle_id = str(payload.get("bundle_id") or "")
    if bundle_id not in BUNDLES:
        raise HTTPException(400, "unknown consent bundle %r" % bundle_id)
    existing = active_consent(db, pid, bundle_id)
    if existing:
        return {"status": "already_granted", "id": existing.consent_id}
    spec = BUNDLES[bundle_id]
    row = ConsentArtefact(
        consent_id=nid("cn"),
        principal_pseudonym=pid,
        bundle_id=bundle_id,
        purpose_string=str(payload.get("purpose_string") or spec["purpose_key"]),
        data_categories=payload.get("data_categories") or spec["data_categories"],
        language=str(payload.get("language") or "en"),
        consent_version="v1",
        granted_at=_now(),
        artefact_hash=nid("h"),
    )
    db.add(row)
    db.flush()
    write_audit(
        db,
        actor=user,
        action="consent.grant",
        resource_type="consent_artefact",
        resource_id=row.consent_id,
        subject_pseudonym_id=pid,
        purpose=row.purpose_string,
    )
    return {"status": "written", "id": row.consent_id}


#: Which consent bundle gates which queued table. A queued row whose scope was
#: withdrawn while it sat offline is DROPPED, not written — the consent state at
#: sync time wins (design-client-apps §2).
GATE = {
    "checkin": "checkin",
    "instrument": "instruments",
    "passive": "passive",
    "voice": "voice",
    "pulse": "unit_pulse",
}


@router.post("/app/sync")
def sync_batch(
    body: SyncBatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    """Drain the client outbox in one request (ADR-0005).

    Idempotent by ``client_uuid``: an item already accepted is reported
    ``duplicate`` and NOT rewritten, so a retry after a lost response can never
    duplicate a row (TC-603). Partial failure is reported per item so the client
    resumes from the last checkpoint rather than replaying the whole queue
    (TC-602); nothing is ever silently dropped without a reason.
    """
    pid = user.pseudonym_id
    if not pid:
        raise HTTPException(400, "principal has no pseudonym")
    results = []
    accepted = 0
    for item in body.items:
        receipt = (
            db.query(SyncReceipt)
            .filter(SyncReceipt.pseudonym_id == pid, SyncReceipt.client_uuid == item.client_uuid)
            .one_or_none()
        )
        if receipt is not None:
            results.append(
                {
                    "client_uuid": item.client_uuid,
                    "table": item.table,
                    "status": "duplicate",
                    "id": receipt.resource_id,
                }
            )
            accepted += 1
            continue

        gate = GATE.get(item.table)
        if gate and not active_consent(db, pid, gate):
            results.append(
                {
                    "client_uuid": item.client_uuid,
                    "table": item.table,
                    "status": "dropped_no_consent",
                    "reason_key": "sync.dropped.consent",
                }
            )
            accepted += 1
            continue

        try:
            if item.table == "checkin":
                outcome = _apply_checkin(db, pid, item.payload)
            elif item.table == "instrument":
                outcome = _apply_instrument(db, pid, item.payload)
            elif item.table == "passive":
                outcome = _apply_passive(db, pid, item.payload)
            elif item.table == "voice":
                outcome = _apply_voice(db, pid, item.payload)
            elif item.table == "pulse":
                outcome = _apply_pulse(db, pid, item.payload)
            elif item.table == "consent":
                outcome = _apply_consent(db, pid, item.payload, user)
            else:
                results.append(
                    {
                        "client_uuid": item.client_uuid,
                        "table": item.table,
                        "status": "rejected",
                        "reason": "unknown table",
                    }
                )
                continue
        except HTTPException as exc:
            # Report and keep going: one bad item must not block the queue.
            results.append(
                {
                    "client_uuid": item.client_uuid,
                    "table": item.table,
                    "status": "rejected",
                    "reason": str(exc.detail),
                }
            )
            continue

        db.add(
            SyncReceipt(
                id=nid("sr"),
                pseudonym_id=pid,
                client_uuid=item.client_uuid,
                table_name=item.table,
                resource_id=outcome.get("id"),
                created_at=_now(),
            )
        )
        db.flush()
        results.append({"client_uuid": item.client_uuid, "table": item.table, **outcome})
        accepted += 1

    write_audit(
        db,
        actor=user,
        action="app.sync",
        resource_type="sync_batch",
        subject_pseudonym_id=pid,
        purpose="voluntary_capture",
        payload={"items": len(body.items), "accepted": accepted},
    )
    return {"results": results, "accepted": accepted, "received": len(body.items)}


# ---------------------------------------------------------------------------
# Roster-first home (F02 screen 1) — read-only HR proxies over kv's ingest tables
# ---------------------------------------------------------------------------


@router.get("/app/roster")
def my_roster(
    days: int = Query(14, ge=1, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    day = as_of()
    rows = (
        db.query(HrDutyRoster)
        .filter(
            HrDutyRoster.pseudonym_id == user.pseudonym_id,
            HrDutyRoster.duty_date >= day - timedelta(days=days),
            HrDutyRoster.duty_date <= day + timedelta(days=days),
        )
        .order_by(HrDutyRoster.duty_date.asc())
        .all()
    )
    upcoming = [r for r in rows if r.duty_date >= day and not r.rest_day]
    return {
        "as_of": day.isoformat(),
        "next_duty": (
            {
                "date": upcoming[0].duty_date.isoformat(),
                "shift_code": upcoming[0].shift_code,
                "unit_id": upcoming[0].unit_id,
            }
            if upcoming
            else None
        ),
        "days": [
            {
                "date": r.duty_date.isoformat(),
                "shift_code": r.shift_code,
                "rest_day": r.rest_day,
                "unit_id": r.unit_id,
            }
            for r in rows
        ],
        "source": "hrms_proxy",
    }


@router.get("/app/leave")
def my_leave(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    rows = (
        db.query(HrLeaveRecord)
        .filter(HrLeaveRecord.pseudonym_id == user.pseudonym_id)
        .order_by(HrLeaveRecord.applied_at.desc())
        .all()
    )
    taken = 0
    for r in rows:
        if r.cancelled_at is None and r.sanctioned_from and r.sanctioned_to:
            taken += (r.sanctioned_to - r.sanctioned_from).days + 1
    entitlement = 30
    return {
        "balance_days": max(0, entitlement - taken),
        "entitlement_days": entitlement,
        "taken_days": taken,
        "applications": [
            {
                "leave_type": r.leave_type,
                "home_leave": r.home_leave,
                "applied_at": r.applied_at.isoformat(),
                "from": r.sanctioned_from.isoformat() if r.sanctioned_from else None,
                "to": r.sanctioned_to.isoformat() if r.sanctioned_to else None,
                "cancelled_at": r.cancelled_at.isoformat() if r.cancelled_at else None,
                "status": (
                    "cancelled"
                    if r.cancelled_at
                    else ("sanctioned" if r.sanctioned_from else "applied")
                ),
            }
            for r in rows
        ],
        "source": "hrms_proxy",
    }


@router.get("/app/payslip")
def my_payslip(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    """Demo-only stub: the HRMS pay proxy is out of scope for v1 (F02 API
    surface). Shape is real so APP-002 swaps the adapter, not the screen."""
    day = as_of()
    month = day.replace(day=1) - timedelta(days=1)
    ident = db.query(IdentityMap).filter(IdentityMap.pseudonym_id == user.pseudonym_id).one_or_none()
    return {
        "month": month.strftime("%Y-%m"),
        "rank": ident.rank if ident else None,
        "available": False,
        "reason_key": "roster.demoNote",
        "source": "demo_stub",
    }


# ---------------------------------------------------------------------------
# F03 screens 3-4 · F02 screen 4 · notifications
# ---------------------------------------------------------------------------


@router.get("/app/signals/summary")
def signals_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    """"What does the server hold about me, per scope, and until when?"
    (F03 screen 4 / FR-18). Raw self-reports expire; derived trends persist."""
    pid = user.pseudonym_id
    ttl = get_settings().raw_ttl_days
    checkins = db.query(CheckIn).filter(CheckIn.pseudonym_id == pid, CheckIn.purged.is_(False)).all()
    instruments = (
        db.query(InstrumentResult)
        .filter(InstrumentResult.pseudonym_id == pid, InstrumentResult.purged.is_(False))
        .all()
    )
    passive = db.query(PassiveFeature).filter(PassiveFeature.pseudonym_id == pid).all()
    voice = (
        db.query(VoiceFeature)
        .filter(VoiceFeature.pseudonym_id == pid, VoiceFeature.purged.is_(False))
        .all()
    )
    pulses = db.query(UnitPulseRating).filter(UnitPulseRating.pseudonym_id == pid).all()

    def _scope(bundle_id: str, rows: list, expiry_attr: str | None) -> dict[str, Any]:
        expires = None
        if expiry_attr and rows:
            values = [getattr(r, expiry_attr) for r in rows if getattr(r, expiry_attr, None)]
            if values:
                expires = min(values).isoformat()
        return {
            "bundle_id": bundle_id,
            "label_key": BUNDLES[bundle_id]["label_key"],
            "rows_held": len(rows),
            "oldest_expiry": expires,
            "granted": active_consent(db, pid, bundle_id) is not None,
        }

    return {
        "raw_ttl_days": ttl,
        "explain_key": "expiry.explain",
        "scopes": [
            _scope("checkin", checkins, "expires_at"),
            _scope("instruments", instruments, "expires_at"),
            _scope("passive", passive, None),
            _scope("voice", voice, "expires_at"),
            _scope("unit_pulse", pulses, None),
        ],
        "raw_audio_held": False,
        "transcripts_held": False,
    }


@router.get("/app/me/checkins")
def my_checkins(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    day = as_of()
    rows = (
        db.query(CheckIn)
        .filter(
            CheckIn.pseudonym_id == user.pseudonym_id,
            CheckIn.purged.is_(False),
            CheckIn.recorded_at >= day - timedelta(days=days),
        )
        .order_by(CheckIn.recorded_at.asc())
        .all()
    )
    return {
        "as_of": day.isoformat(),
        "checked_in_today": any(r.recorded_at == day for r in rows),
        "checkins": [
            {
                "date": r.recorded_at.isoformat(),
                "mood_label": r.mood_label,
                "mood_score": r.mood_score,
                "sleep_hours": r.sleep_hours,
                "expires_at": r.expires_at.isoformat(),
            }
            for r in rows
        ],
        "disclaimer_key": "instr.not_diagnosis",
        "own_only_key": "trend.ownonly",
    }


@router.get("/app/me/instruments")
def my_instruments(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    day = as_of()
    month_start = day.replace(day=1)
    rows = (
        db.query(InstrumentResult)
        .filter(
            InstrumentResult.pseudonym_id == user.pseudonym_id,
            InstrumentResult.purged.is_(False),
        )
        .order_by(InstrumentResult.recorded_at.desc())
        .all()
    )
    done_this_month = {r.instrument for r in rows if r.recorded_at >= month_start}
    return {
        "instruments": list(INSTRUMENTS),
        "done_this_month": sorted(done_this_month),
        "done_key": "instrument.done",
        "history": [
            {
                "instrument": r.instrument,
                "score": r.score,
                "date": r.recorded_at.isoformat(),
            }
            for r in rows
        ],
        "disclaimer_key": "screen.disclaimer",
    }


@router.get("/app/notifications")
def my_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("jawan")),
):
    rows = (
        db.query(Notification)
        .filter(Notification.recipient_pseudonym == user.pseudonym_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "notifications": [
            {
                "id": r.id,
                "kind": r.kind,
                "body_key": r.body_key,
                "payload": r.payload,
                "created_at": r.created_at.isoformat(),
                "read": r.read_at is not None,
            }
            for r in rows
        ]
    }


# ---------------------------------------------------------------------------
# Own check-in for non-jawan principals (F07 screen 6, officer-first rollout)
# ---------------------------------------------------------------------------


class OwnCheckInIn(BaseModel):
    mood_label: str | None = None
    mood_score: int | None = Field(default=None, ge=0, le=10)
    sleep_hours: float | None = None
    recorded_at: str | None = None


@router.post("/me/checkins")
def own_checkin(
    body: OwnCheckInIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Self-scope only, for every role. This route deliberately sits OUTSIDE
    ``/app`` so a commander can take their own check-in without the ADR-0003
    middleware having to make an exception for the individual-welfare prefix.
    It accepts no subject selector, so there is no shape in which it could
    return someone else's data."""
    pid = _self_pseudonym(db, user)
    result = _apply_checkin(db, pid, body.model_dump())
    write_audit(
        db,
        actor=user,
        action="app.own_checkin",
        resource_type="checkins",
        resource_id=result.get("id"),
        subject_pseudonym_id=pid,
        purpose="voluntary_capture",
    )
    return {**result, "self_scope": True}


@router.get("/me/checkins")
def own_checkins(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pid = user.pseudonym_id
    day = as_of()
    if not pid:
        return {"as_of": day.isoformat(), "checked_in_today": False, "checkins": []}
    rows = (
        db.query(CheckIn)
        .filter(
            CheckIn.pseudonym_id == pid,
            CheckIn.purged.is_(False),
            CheckIn.recorded_at >= day - timedelta(days=days),
        )
        .order_by(CheckIn.recorded_at.asc())
        .all()
    )
    return {
        "as_of": day.isoformat(),
        "checked_in_today": any(r.recorded_at == day for r in rows),
        "checkins": [
            {"date": r.recorded_at.isoformat(), "mood_score": r.mood_score} for r in rows
        ],
        "self_scope": True,
    }
