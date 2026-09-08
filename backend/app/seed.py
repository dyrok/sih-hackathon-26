"""Deterministic demo seed — DEMO-PERSONA-01 Constable, 34, 3rd Bn (F09 arc)."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .clock import as_of, set_as_of
from .config import get_settings
from .ids import nid
from .models import (
    CheckIn,
    ConsentArtefact,
    HrDeployment,
    HrDutyRoster,
    HrIncident,
    HrLeaveRecord,
    HrTransfer,
    IdentityMap,
    PassiveFeature,
    User,
)
from .passwords import hash_password
from .risk.scorer import score_person
from .signals.snapshot import recompute_all

DEMO_PASSWORD = "saarthi"
ARC_START = date(2026, 6, 4)  # day 1; day 90 = 2026-09-01
PERSONA_PERSONNEL = "CR-DEMO-01"
PERSONA_PSEUDONYM = "ps_demo01"
UNIT_3BN = "3BN"
UNIT_TINY = "TINY"


def day(n: int) -> date:
    return ARC_START + timedelta(days=n - 1)


def _user(db: Session, **kwargs) -> User:
    existing = db.query(User).filter(User.username == kwargs["username"]).one_or_none()
    if existing:
        return existing
    row = User(password_hash=hash_password(DEMO_PASSWORD), is_active=True, **kwargs)
    db.add(row)
    db.flush()
    return row


def _ident(db: Session, **kwargs) -> IdentityMap:
    existing = db.get(IdentityMap, kwargs["personnel_id"])
    if existing:
        return existing
    row = IdentityMap(**kwargs)
    db.add(row)
    db.flush()
    return row


def seed_users_and_identities(db: Session) -> None:
    _ident(
        db,
        personnel_id=PERSONA_PERSONNEL,
        pseudonym_id=PERSONA_PSEUDONYM,
        unit_id=UNIT_3BN,
        rank="Constable",
        age=34,
        legal_name="Demo Constable",
        skill_tags=["general"],
    )
    for i in range(2, 13):
        _ident(
            db,
            personnel_id=f"CR-3BN-{i:02d}",
            pseudonym_id=f"ps_3bn{i:02d}",
            unit_id=UNIT_3BN,
            rank="Constable" if i < 10 else "Head Constable",
            age=24 + i,
            legal_name=f"Jawan {i}",
            skill_tags=["general"],
        )
    for i in range(1, 5):
        _ident(
            db,
            personnel_id=f"CR-TINY-{i}",
            pseudonym_id=f"ps_tiny{i}",
            unit_id=UNIT_TINY,
            rank="Constable",
            age=25,
            legal_name=f"Tiny {i}",
            skill_tags=["general"],
        )

    _user(
        db,
        id="usr_jawan_demo",
        username="jawan.demo",
        role="jawan",
        unit_id=UNIT_3BN,
        personnel_id=PERSONA_PERSONNEL,
        pseudonym_id=PERSONA_PSEUDONYM,
        display_name="Demo Constable",
    )
    _user(
        db,
        id="usr_counsellor_a",
        username="counsellor.a",
        role="counsellor",
        display_name="Counsellor A",
    )
    _user(
        db,
        id="usr_welfare_a",
        username="welfare.a",
        role="welfare_officer",
        unit_id=UNIT_3BN,
        assigned_units=[UNIT_3BN],
        display_name="Welfare Officer A",
    )
    _user(
        db,
        id="usr_cmd_3bn",
        username="commander.3bn",
        role="commander",
        unit_id=UNIT_3BN,
        display_name="CO 3rd Bn",
    )
    _user(
        db,
        id="usr_cmd_tiny",
        username="commander.tiny",
        role="commander",
        unit_id=UNIT_TINY,
        display_name="CO Tiny",
    )
    _user(db, id="usr_admin", username="admin", role="admin", display_name="Admin")
    _user(db, id="usr_auditor", username="auditor", role="auditor", display_name="Auditor")
    _user(db, id="usr_hr", username="hr.ingest", role="hr_ingest", display_name="HR ingest")
    _user(
        db,
        id="usr_jawan_tiny",
        username="jawan.tiny",
        role="jawan",
        unit_id=UNIT_TINY,
        personnel_id="CR-TINY-1",
        pseudonym_id="ps_tiny1",
        display_name="Tiny 1",
    )


def seed_persona_hr(db: Session) -> None:
    pid = PERSONA_PSEUDONYM
    if db.query(HrDutyRoster).filter(HrDutyRoster.pseudonym_id == pid).first():
        return
    # 90 duty days, no rest — cancelled leave must not reset the streak.
    for n in range(1, 91):
        d = day(n)
        night = 40 <= n <= 50
        db.add(
            HrDutyRoster(
                id=nid("dt"),
                pseudonym_id=pid,
                unit_id=UNIT_3BN,
                duty_date=d,
                shift_code="night" if night else "day",
                rest_day=False,
            )
        )
    # Home leave completed well before the arc so L1 is large (Green baseline still holds early).
    db.add(
        HrLeaveRecord(
            id=nid("lv"),
            pseudonym_id=pid,
            leave_type="home_leave",
            home_leave=True,
            applied_at=date(2025, 11, 1),
            sanctioned_from=date(2025, 11, 10),
            sanctioned_to=date(2025, 11, 24),
            actual_return_date=date(2025, 11, 24),
        )
    )
    db.add(
        HrLeaveRecord(
            id=nid("lv"),
            pseudonym_id=pid,
            leave_type="home_leave",
            home_leave=True,
            applied_at=day(31),
            cancelled_at=day(31),
        )
    )
    db.add(
        HrLeaveRecord(
            id=nid("lv"),
            pseudonym_id=pid,
            leave_type="home_leave",
            home_leave=True,
            applied_at=day(55),
            cancelled_at=day(55),
        )
    )
    db.add(
        HrDeployment(
            id=nid("dp"),
            pseudonym_id=pid,
            unit_id=UNIT_3BN,
            posting_type="high_risk",
            start_date=date(2025, 12, 1),
            end_date=None,
            distance_km=850,
        )
    )
    db.add(
        HrTransfer(
            id=nid("xf"),
            pseudonym_id=pid,
            from_unit="1BN",
            to_unit=UNIT_3BN,
            effective_date=date(2026, 1, 15),
            reason_code="posting",
        )
    )
    db.add(
        HrTransfer(
            id=nid("xf"),
            pseudonym_id=pid,
            from_unit="2BN",
            to_unit="1BN",
            effective_date=date(2025, 10, 1),
            reason_code="posting",
        )
    )
    # Sleep series: 7h baseline, then −30% in the trailing 7-day window from day 56.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    settings = get_settings()
    for n in range(1, 91):
        hours = 4.9 if n >= 56 else 7.0
        if n == 64:
            hours = 4.0
        d = day(n)
        db.add(
            CheckIn(
                id=nid("ck"),
                pseudonym_id=pid,
                recorded_at=d,
                mood_label="fine" if n == 64 else "ok",
                mood_score=5 if n == 64 else 3,
                sleep_hours=hours,
                expires_at=d + timedelta(days=settings.raw_ttl_days),
                purged=False,
            )
        )
        db.add(
            PassiveFeature(
                id=nid("pf"),
                pseudonym_id=pid,
                sleep_hours_proxy=hours,
                recorded_at=d,
            )
        )
    if db.query(ConsentArtefact).filter(ConsentArtefact.principal_pseudonym == pid).first() is None:
        db.add(
            ConsentArtefact(
                consent_id=nid("cn"),
                principal_pseudonym=pid,
                bundle_id="checkin",
                purpose_string="wellness_self_report",
                data_categories=["checkin", "sleep", "instruments"],
                language="hi",
                consent_version="v1",
                granted_at=now,
                artefact_hash=nid("h"),
            )
        )
        db.add(
            ConsentArtefact(
                consent_id=nid("cn"),
                principal_pseudonym=pid,
                bundle_id="instruments",
                purpose_string="wellness_self_report",
                data_categories=["PHQ-9"],
                language="hi",
                consent_version="v1",
                granted_at=now,
                artefact_hash=nid("h"),
            )
        )
        db.add(
            ConsentArtefact(
                consent_id=nid("cn"),
                principal_pseudonym=pid,
                bundle_id="passive",
                purpose_string="on_device_features",
                data_categories=["sleep_proxy"],
                language="hi",
                consent_version="v1",
                granted_at=now,
                artefact_hash=nid("h"),
            )
        )


def seed_unit_background(db: Session) -> None:
    others = db.query(IdentityMap).filter(IdentityMap.unit_id == UNIT_3BN, IdentityMap.pseudonym_id != PERSONA_PSEUDONYM).all()
    if db.query(HrDutyRoster).filter(HrDutyRoster.pseudonym_id == "ps_3bn02").first():
        return
    for p in others:
        for n in range(1, 91):
            d = day(n)
            rest = n % 7 == 0
            db.add(
                HrDutyRoster(
                    id=nid("dt"),
                    pseudonym_id=p.pseudonym_id,
                    unit_id=UNIT_3BN,
                    duty_date=d,
                    shift_code="day",
                    rest_day=rest,
                )
            )
        db.add(
            HrLeaveRecord(
                id=nid("lv"),
                pseudonym_id=p.pseudonym_id,
                leave_type="home_leave",
                home_leave=True,
                applied_at=day(5),
                sanctioned_from=day(10),
                sanctioned_to=day(20),
                actual_return_date=day(20),
            )
        )
    tinies = db.query(IdentityMap).filter(IdentityMap.unit_id == UNIT_TINY).all()
    for p in tinies:
        for n in range(1, 15):
            db.add(
                HrDutyRoster(
                    id=nid("dt"),
                    pseudonym_id=p.pseudonym_id,
                    unit_id=UNIT_TINY,
                    duty_date=day(n),
                    shift_code="day",
                    rest_day=False,
                )
            )


def seed_incident(db: Session) -> None:
    if db.get(HrIncident, "INC-3BN-01"):
        return
    db.add(
        HrIncident(
            incident_id="INC-3BN-01",
            unit_id=UNIT_3BN,
            incident_type="casualty",
            severity_band="high",
            incident_date=day(80),
            exposure_window_days=30,
        )
    )


def seed_demo(db: Session, score: bool = True) -> None:
    set_as_of(get_settings().as_of_date())
    seed_users_and_identities(db)
    seed_persona_hr(db)
    seed_unit_background(db)
    seed_incident(db)
    db.flush()
    recompute_all(db, as_of())
    if score:
        for ident in db.query(IdentityMap).all():
            score_person(db, ident.pseudonym_id, as_of=as_of())
    db.flush()


def main() -> None:
    from .db import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        seed_demo(db)
        db.commit()
        print("seeded demo data; login jawan.demo / saarthi")
    finally:
        db.close()


if __name__ == "__main__":
    main()
