from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

DATASETS = ("leave", "roster", "deployment", "transfer", "incident", "medical", "career")


def parse_date(value: Any) -> date | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


class LeaveIn(BaseModel):
    personnel_id: str
    leave_type: str
    home_leave: bool = False
    applied_at: date
    sanctioned_from: date | None = None
    sanctioned_to: date | None = None
    cancelled_at: date | None = None
    denial_reason: str | None = None
    actual_return_date: date | None = None

    @field_validator("applied_at", "sanctioned_from", "sanctioned_to", "cancelled_at", "actual_return_date", mode="before")
    @classmethod
    def _d(cls, v):
        return parse_date(v)

    @field_validator("home_leave", mode="before")
    @classmethod
    def _b(cls, v):
        return parse_bool(v)


class RosterIn(BaseModel):
    personnel_id: str
    unit_id: str
    duty_date: date
    shift_code: str = "day"
    rest_day: bool = False

    @field_validator("duty_date", mode="before")
    @classmethod
    def _d(cls, v):
        return parse_date(v)

    @field_validator("rest_day", mode="before")
    @classmethod
    def _b(cls, v):
        return parse_bool(v)


class DeploymentIn(BaseModel):
    personnel_id: str
    unit_id: str
    posting_type: str
    start_date: date
    end_date: date | None = None
    distance_km: float | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _d(cls, v):
        return parse_date(v)


class TransferIn(BaseModel):
    personnel_id: str
    from_unit: str
    to_unit: str
    effective_date: date
    reason_code: str | None = None

    @field_validator("effective_date", mode="before")
    @classmethod
    def _d(cls, v):
        return parse_date(v)


class IncidentIn(BaseModel):
    incident_id: str
    unit_id: str
    incident_type: str
    severity_band: str = "other"
    incident_date: date
    exposure_window_days: int = 30

    @field_validator("incident_date", mode="before")
    @classmethod
    def _d(cls, v):
        return parse_date(v)


class MedicalIn(BaseModel):
    personnel_id: str
    visit_date: date
    visit_type: str
    injury_flag: bool = False

    @field_validator("visit_date", mode="before")
    @classmethod
    def _d(cls, v):
        return parse_date(v)

    @field_validator("injury_flag", mode="before")
    @classmethod
    def _b(cls, v):
        return parse_bool(v)


class CareerIn(BaseModel):
    personnel_id: str
    promotion_board_pending_months: float | None = None
    inquiry_court_pending: bool = False
    inquiry_age_days: int | None = None
    denied_training_count_12m: int = 0

    @field_validator("inquiry_court_pending", mode="before")
    @classmethod
    def _b(cls, v):
        return parse_bool(v)


class BatchIn(BaseModel):
    batch_id: str
    rows: list[dict] = Field(default_factory=list)


SCHEMA_BY_DATASET = {
    "leave": LeaveIn,
    "roster": RosterIn,
    "deployment": DeploymentIn,
    "transfer": TransferIn,
    "incident": IncidentIn,
    "medical": MedicalIn,
    "career": CareerIn,
}
