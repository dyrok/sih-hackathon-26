from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=True, index=True)
    assigned_units = Column(JSON, nullable=True)  # welfare officer
    personnel_id = Column(String, nullable=True, unique=True)
    pseudonym_id = Column(String, nullable=True, index=True)
    display_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class IdentityMap(Base):
    """F08 identity vault — analytics never join this without dual-key."""

    __tablename__ = "identity_map"

    personnel_id = Column(String, primary_key=True)
    pseudonym_id = Column(String, unique=True, nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)
    rank = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    legal_name = Column(String, nullable=False)
    skill_tags = Column(JSON, nullable=True)


class ConsentArtefact(Base):
    __tablename__ = "consent_artefacts"

    consent_id = Column(String, primary_key=True)
    principal_pseudonym = Column(String, nullable=False, index=True)
    bundle_id = Column(String, nullable=False)
    purpose_string = Column(String, nullable=False)
    data_categories = Column(JSON, nullable=False)
    language = Column(String, nullable=False, default="en")
    consent_version = Column(String, nullable=False, default="v1")
    granted_at = Column(DateTime, nullable=False)
    withdrawn_at = Column(DateTime, nullable=True)
    artefact_hash = Column(String, nullable=False)


class IngestBatch(Base):
    __tablename__ = "ingest_batch"

    batch_id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    rows_in = Column(Integer, nullable=False, default=0)
    rows_written = Column(Integer, nullable=False, default=0)
    rows_quarantined = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="received")
    received_at = Column(DateTime, nullable=False)
    batch_hash = Column(String, nullable=True)
    #: Who submitted it. Without this the quarantine report is addressable by a
    #: guessable batch id from any ingest account (TC-424).
    submitted_by_user_id = Column(String, nullable=True, index=True)


class QuarantineRow(Base):
    __tablename__ = "quarantine_row"

    id = Column(String, primary_key=True)
    batch_id = Column(String, ForeignKey("ingest_batch.batch_id"), nullable=False, index=True)
    dataset = Column(String, nullable=False)
    row_index = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    reason = Column(String, nullable=False)


class HrLeaveRecord(Base):
    __tablename__ = "hr_leave_record"
    __table_args__ = (
        UniqueConstraint("pseudonym_id", "applied_at", "leave_type", name="uq_leave_nat"),
    )

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    leave_type = Column(String, nullable=False)
    home_leave = Column(Boolean, nullable=False, default=False)
    applied_at = Column(Date, nullable=False)
    sanctioned_from = Column(Date, nullable=True)
    sanctioned_to = Column(Date, nullable=True)
    cancelled_at = Column(Date, nullable=True)
    denial_reason = Column(String, nullable=True)
    actual_return_date = Column(Date, nullable=True)
    batch_id = Column(String, nullable=True)


class HrDutyRoster(Base):
    __tablename__ = "hr_duty_roster"
    __table_args__ = (UniqueConstraint("pseudonym_id", "duty_date", name="uq_duty_nat"),)

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)
    duty_date = Column(Date, nullable=False, index=True)
    shift_code = Column(String, nullable=False)
    rest_day = Column(Boolean, nullable=False, default=False)
    batch_id = Column(String, nullable=True)


class HrDeployment(Base):
    __tablename__ = "hr_deployment"
    __table_args__ = (
        UniqueConstraint("pseudonym_id", "start_date", "posting_type", name="uq_dep_nat"),
    )

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=False)
    posting_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    distance_km = Column(Float, nullable=True)
    batch_id = Column(String, nullable=True)


class HrTransfer(Base):
    __tablename__ = "hr_transfer"
    __table_args__ = (
        UniqueConstraint("pseudonym_id", "effective_date", "from_unit", "to_unit", name="uq_xfer_nat"),
    )

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    from_unit = Column(String, nullable=False)
    to_unit = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False)
    reason_code = Column(String, nullable=True)
    batch_id = Column(String, nullable=True)


class HrIncident(Base):
    __tablename__ = "hr_incident"

    incident_id = Column(String, primary_key=True)
    unit_id = Column(String, nullable=False, index=True)
    incident_type = Column(String, nullable=False)
    severity_band = Column(String, nullable=False)
    incident_date = Column(Date, nullable=False)
    exposure_window_days = Column(Integer, nullable=False, default=30)
    batch_id = Column(String, nullable=True)


class HrMedical(Base):
    __tablename__ = "hr_medical"
    __table_args__ = (
        UniqueConstraint("pseudonym_id", "visit_date", "visit_type", name="uq_med_nat"),
    )

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    visit_date = Column(Date, nullable=False)
    visit_type = Column(String, nullable=False)
    injury_flag = Column(Boolean, nullable=False, default=False)
    batch_id = Column(String, nullable=True)


class HrCareerState(Base):
    __tablename__ = "hr_career_state"

    pseudonym_id = Column(String, primary_key=True)
    promotion_board_pending_months = Column(Float, nullable=True)
    inquiry_court_pending = Column(Boolean, nullable=False, default=False)
    inquiry_age_days = Column(Integer, nullable=True)
    denied_training_count_12m = Column(Integer, nullable=False, default=0)


class SignalSnapshot(Base):
    __tablename__ = "signal_snapshot"
    __table_args__ = (
        UniqueConstraint("pseudonym_id", "signal_key", "window_end", name="uq_snap"),
        Index("ix_snap_person", "pseudonym_id"),
    )

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False)
    signal_key = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    window_start = Column(Date, nullable=False)
    window_end = Column(Date, nullable=False)
    computed_at = Column(DateTime, nullable=False)
    engine_version = Column(String, nullable=False)
    source_batch = Column(String, nullable=True)


class SignalGroupFlag(Base):
    __tablename__ = "signal_group_flag"
    __table_args__ = (
        UniqueConstraint("unit_id", "signal_key", "incident_id", name="uq_group_flag"),
    )

    id = Column(String, primary_key=True)
    unit_id = Column(String, nullable=False, index=True)
    signal_key = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    incident_id = Column(String, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)


class CheckIn(Base):
    __tablename__ = "checkins"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    recorded_at = Column(Date, nullable=False)
    mood_label = Column(String, nullable=True)
    mood_score = Column(Integer, nullable=True)
    sleep_hours = Column(Float, nullable=True)
    expires_at = Column(Date, nullable=False)
    purged = Column(Boolean, nullable=False, default=False)


class InstrumentResult(Base):
    __tablename__ = "instrument_results"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    instrument = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    item_9 = Column(Integer, nullable=True)
    validity_fail = Column(Boolean, nullable=False, default=False)
    straight_lining = Column(Boolean, nullable=False, default=False)
    too_fast = Column(Boolean, nullable=False, default=False)
    all_max = Column(Boolean, nullable=False, default=False)
    recorded_at = Column(Date, nullable=False)
    expires_at = Column(Date, nullable=False)
    purged = Column(Boolean, nullable=False, default=False)


class PassiveFeature(Base):
    __tablename__ = "passive_features"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    sleep_hours_proxy = Column(Float, nullable=True)
    recorded_at = Column(Date, nullable=False)


class RiskScore(Base):
    __tablename__ = "risk_score"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    score = Column(Integer, nullable=False)
    tier = Column(String, nullable=False, index=True)
    confidence = Column(String, nullable=False)
    engine_version = Column(String, nullable=False)
    ruleset_version = Column(Integer, nullable=False)
    computed_at = Column(DateTime, nullable=False)
    as_of = Column(Date, nullable=False)
    sources_present = Column(JSON, nullable=False)
    stale = Column(Boolean, nullable=False, default=False)
    hysteresis_held = Column(Boolean, nullable=False, default=False)
    #: The tier the rules produced BEFORE hysteresis. Without it the downgrade
    #: counter reads its own held output and can never reach the confirmations
    #: it is waiting for — a person who recovers stays flagged forever.
    candidate_tier = Column(String, nullable=True)

    factors = relationship("RiskFactor", back_populates="score_row", cascade="all, delete-orphan")
    masking = relationship("MaskingFlag", back_populates="score_row", uselist=False)


class RiskFactor(Base):
    __tablename__ = "risk_factor"

    id = Column(String, primary_key=True)
    score_id = Column(String, ForeignKey("risk_score.id"), nullable=False, index=True)
    rule_id = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    observed_value = Column(String, nullable=True)
    display_key = Column(String, nullable=False)
    display_value = Column(String, nullable=True)

    score_row = relationship("RiskScore", back_populates="factors")


class PersonBaseline(Base):
    __tablename__ = "person_baseline"
    __table_args__ = (UniqueConstraint("pseudonym_id", "signal_key", name="uq_baseline"),)

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False)
    signal_key = Column(String, nullable=False)
    window_days = Column(Integer, nullable=False)
    baseline_mean = Column(Float, nullable=True)
    deviation = Column(Float, nullable=True)
    change_point_at = Column(Date, nullable=True)
    history_days = Column(Integer, nullable=False, default=0)


class MaskingFlag(Base):
    __tablename__ = "masking_flag"

    id = Column(String, primary_key=True)
    score_id = Column(String, ForeignKey("risk_score.id"), nullable=False, unique=True)
    matched_conditions = Column(JSON, nullable=False)
    tier_floor = Column(String, nullable=False)

    score_row = relationship("RiskScore", back_populates="masking")


class GroupExposureLink(Base):
    __tablename__ = "group_exposure_link"

    id = Column(String, primary_key=True)
    score_id = Column(String, ForeignKey("risk_score.id"), nullable=False)
    incident_id = Column(String, nullable=False)


class ResponseCase(Base):
    __tablename__ = "response_case"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=True, index=True)
    score_id = Column(String, nullable=True)
    unit_id = Column(String, nullable=True, index=True)
    tier = Column(String, nullable=False)
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="open")
    group_case = Column(Boolean, nullable=False, default=False)
    incident_id = Column(String, nullable=True)
    sla_hours = Column(Integer, nullable=True)


class TriageEntry(Base):
    __tablename__ = "triage_entry"

    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("response_case.id"), nullable=False, index=True)
    urgency = Column(Float, nullable=False)
    intervenability = Column(Float, nullable=False)
    priority = Column(Float, nullable=False)
    deferred_until = Column(Date, nullable=True)
    assigned_counsellor_id = Column(String, nullable=True)
    cap_reason = Column(String, nullable=True)


class AlertBudgetLedger(Base):
    __tablename__ = "alert_budget_ledger"
    __table_args__ = (UniqueConstraint("counsellor_id", "week_start", name="uq_budget"),)

    id = Column(String, primary_key=True)
    counsellor_id = Column(String, nullable=False)
    week_start = Column(Date, nullable=False)
    alerts_used = Column(Integer, nullable=False, default=0)
    cap = Column(Integer, nullable=False)


class InterventionAction(Base):
    __tablename__ = "intervention_action"

    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("response_case.id"), nullable=False, index=True)
    catalogue_id = Column(String, nullable=False)
    actor_role = Column(String, nullable=False)
    initiated_at = Column(DateTime, nullable=False)
    due_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="open")


class RosterSwapProposal(Base):
    __tablename__ = "roster_swap_proposal"

    id = Column(String, primary_key=True)
    unit_id = Column(String, nullable=False, index=True)
    mode = Column(String, nullable=False)
    input_roster_version = Column(String, nullable=False)
    proposed_swaps = Column(JSON, nullable=False)
    max_load_before = Column(Float, nullable=False)
    max_load_after = Column(Float, nullable=False)
    infeasible_shifts = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="proposed")
    approved_by_role = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


class TelemanasReferral(Base):
    __tablename__ = "telemanas_referral"

    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("response_case.id"), nullable=False, index=True)
    referred_at = Column(DateTime, nullable=False)
    mode = Column(String, nullable=False)
    outcome_status = Column(String, nullable=False, default="referred")
    updated_at = Column(DateTime, nullable=False)


class InterventionOutcome(Base):
    __tablename__ = "intervention_outcome"

    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("response_case.id"), nullable=False, index=True)
    action_id = Column(String, nullable=True)
    outcome = Column(String, nullable=False)
    recorded_by_role = Column(String, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    label_exported = Column(Boolean, nullable=False, default=False)


class UnmaskRequest(Base):
    __tablename__ = "unmask_request"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=False)
    purpose_string = Column(String, nullable=False)
    counsellor_user_id = Column(String, nullable=True)
    welfare_user_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class BreakGlassEvent(Base):
    __tablename__ = "break_glass_event"

    id = Column(String, primary_key=True)
    counsellor_user_id = Column(String, nullable=False)
    pseudonym_id = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=False)
    opened_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    notified_subject = Column(Boolean, nullable=False, default=True)
    notified_welfare = Column(Boolean, nullable=False, default=True)
    oversight_flag = Column(Boolean, nullable=False, default=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    recipient_user_id = Column(String, nullable=True)
    recipient_pseudonym = Column(String, nullable=True, index=True)
    kind = Column(String, nullable=False)
    body_key = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)
    read_at = Column(DateTime, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    at = Column(DateTime, nullable=False)
    actor_id = Column(String, nullable=True)
    actor_role = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    subject_pseudonym_id = Column(String, nullable=True, index=True)
    denied = Column(Boolean, nullable=False, default=False)
    prev_hash = Column(String, nullable=True)
    entry_hash = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)


# ---------------------------------------------------------------------------
# Client-surface tables (neel — APP-003/005/006/007/008/009/010).
# Additive only: nothing above this line changes. Every table below is either
# self-scoped (subject == token principal) or unit-scoped and k-filtered before
# it leaves the API (ADR-0003).
# ---------------------------------------------------------------------------


class UnitPulseRating(Base):
    """FR-19 anonymous unit pulse. Stored per principal ONLY to enforce
    one-rating-per-facet-per-period; no read path exposes the pseudonym."""

    __tablename__ = "unit_pulse_rating"
    __table_args__ = (
        UniqueConstraint("pseudonym_id", "period", "facet", name="uq_pulse_once"),
        Index("ix_pulse_unit_period", "unit_id", "period"),
    )

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=False)
    period = Column(String, nullable=False)  # ISO week, e.g. 2026-W36
    facet = Column(String, nullable=False)  # leadership | fairness | family | facilities
    rating = Column(Integer, nullable=False)  # 1..5
    recorded_at = Column(Date, nullable=False)


class BuddyPair(Base):
    """F02 screen 7 — battle buddy. Command sees neither side of any pairing."""

    __tablename__ = "buddy_pair"
    __table_args__ = (UniqueConstraint("a_pseudonym", "b_pseudonym", name="uq_buddy_pair"),)

    id = Column(String, primary_key=True)
    a_pseudonym = Column(String, nullable=False, index=True)
    b_pseudonym = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)


class BuddyState(Base):
    """Coarse state only — ok | quiet | sos. Never a score, never a tier."""

    __tablename__ = "buddy_state"

    pseudonym_id = Column(String, primary_key=True)
    state = Column(String, nullable=False, default="ok")
    updated_at = Column(DateTime, nullable=False)


class DutySitrep(Base):
    """Officer's own daily duty log (voice sitrep). Self-scope only.

    The transcript is a *work* artefact the officer chose to file. Tone and
    mood fields are a private heuristic for that same officer — they are never
    joined into unit aggregates and there is no subject selector on the route.
    """

    __tablename__ = "duty_sitreps"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    duty_date = Column(Date, nullable=False, index=True)
    transcript = Column(Text, nullable=False)
    work_summary = Column(Text, nullable=False)
    work_bullets = Column(JSON, nullable=False)
    answers = Column(JSON, nullable=True)
    tone_label = Column(String, nullable=False)
    mood_label = Column(String, nullable=False)
    mood_score = Column(Integer, nullable=False)
    wellness_summary = Column(Text, nullable=False)
    flags = Column(JSON, nullable=False)
    duration_s = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False)


class VoiceFeature(Base):
    """F03 / ADR-0002 — prosody feature vector only. There is deliberately no
    audio, transcript, speaker-embedding or device-fingerprint column here:
    the exclusion is enforced by schema, not by convention."""

    __tablename__ = "voice_feature"

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    recorded_at = Column(Date, nullable=False)
    f0_mean = Column(Float, nullable=True)
    f0_sd = Column(Float, nullable=True)
    speech_rate = Column(Float, nullable=True)
    pause_count = Column(Integer, nullable=True)
    pause_total = Column(Float, nullable=True)
    voiced_ratio = Column(Float, nullable=True)
    loudness_var = Column(Float, nullable=True)
    jitter = Column(Float, nullable=True)
    shimmer = Column(Float, nullable=True)
    duration_s = Column(Float, nullable=False)
    model_version = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    expires_at = Column(Date, nullable=False)
    purged = Column(Boolean, nullable=False, default=False)


class SessionNote(Base):
    """F06 screen 4 — confidential counsellor record (MHCA 2017 §23).
    Never exportable into any appraisal flow; not an ML label input (ADR-0001)."""

    __tablename__ = "session_note"

    id = Column(String, primary_key=True)
    case_id = Column(String, ForeignKey("response_case.id"), nullable=False, index=True)
    author_user_id = Column(String, nullable=False)
    session_at = Column(DateTime, nullable=False)
    modality = Column(String, nullable=False)  # in_person | tele | telemanas
    themes = Column(JSON, nullable=False)
    risk_reestimate = Column(Integer, nullable=True)  # 0..100, counsellor's own
    free_text = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)


class SimulationRun(Base):
    """F07 screen 4 — what-if. Unit IDs exclusively: a scenario object can never
    carry a person. Assumptions are snapshotted so a projection is auditable."""

    __tablename__ = "simulation_run"

    id = Column(String, primary_key=True)
    unit_id = Column(String, nullable=False, index=True)
    scenario_params = Column(JSON, nullable=False)
    projected_deltas = Column(JSON, nullable=False)
    assumption_snapshot = Column(JSON, nullable=False)
    created_by_role = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class SyncReceipt(Base):
    """Idempotency ledger for the offline outbox (ADR-0005 / TC-603).

    One row per (principal, client_uuid) the server has already accepted. A
    retry after a lost response finds its receipt and is reported ``duplicate``
    instead of writing a second row. The uuid is a device-scoped random value
    and carries no PII — it exists only so retries are safe.
    """

    __tablename__ = "sync_receipt"
    __table_args__ = (UniqueConstraint("pseudonym_id", "client_uuid", name="uq_sync_receipt"),)

    id = Column(String, primary_key=True)
    pseudonym_id = Column(String, nullable=False, index=True)
    client_uuid = Column(String, nullable=False, index=True)
    table_name = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


class AuditCheckpoint(Base):
    """External anchor for the audit chain (TC-443).

    A hash chain proves that no entry was *edited*, but not that none was
    *removed from the end* — a truncated chain is still internally consistent.
    This single row records the head hash and the entry count outside the log
    itself, so deleting the tail leaves the checkpoint disagreeing with the
    table. It is exported with the audit bundle, which is what makes it an
    anchor rather than one more row for the same DBA to edit.
    """

    __tablename__ = "audit_checkpoint"

    id = Column(Integer, primary_key=True)
    entry_count = Column(Integer, nullable=False, default=0)
    head_hash = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=False)
