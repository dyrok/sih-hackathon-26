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
