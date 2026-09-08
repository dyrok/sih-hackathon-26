from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class LeaveRow:
    leave_type: str
    home_leave: bool
    applied_at: date
    sanctioned_from: date | None
    sanctioned_to: date | None
    cancelled_at: date | None
    denial_reason: str | None
    actual_return_date: date | None


@dataclass
class DutyRow:
    duty_date: date
    shift_code: str
    rest_day: bool
    unit_id: str


@dataclass
class DeploymentRow:
    posting_type: str
    start_date: date
    end_date: date | None
    distance_km: float | None
    unit_id: str


@dataclass
class TransferRow:
    from_unit: str
    to_unit: str
    effective_date: date
    reason_code: str | None


@dataclass
class MedicalRow:
    visit_date: date
    visit_type: str
    injury_flag: bool


@dataclass
class CareerRow:
    promotion_board_pending_months: float | None
    inquiry_court_pending: bool
    inquiry_age_days: int | None
    denied_training_count_12m: int
