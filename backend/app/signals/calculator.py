from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .domain import career as C
from .domain import deployment as E
from .domain import duty as D
from .domain import events as T
from .domain import health as H
from .domain import leave as L
from .types import CareerRow, DeploymentRow, DutyRow, LeaveRow, MedicalRow, TransferRow


def compute_person_signals(
    *,
    as_of: date,
    leave: list[LeaveRow],
    duty: list[DutyRow],
    deployments: list[DeploymentRow],
    transfers: list[TransferRow],
    medical: list[MedicalRow],
    career: CareerRow | None,
) -> dict[str, float | None]:
    window_start = as_of - timedelta(days=89)
    _ = window_start
    return {
        "days_since_home_leave": L.days_since_home_leave(leave, as_of),
        "leave_cancel_count": L.leave_cancel_count(leave, as_of),
        "leave_denial_count": L.leave_denial_count(leave, as_of),
        "early_return_days": L.early_return_days(leave, as_of),
        "consecutive_duty_days": D.consecutive_duty_days(duty, as_of),
        "night_shift_ratio": D.night_shift_ratio(duty, as_of),
        "rotation_speed_direction": D.rotation_speed_direction(duty, as_of),
        "circadian_disruption_score": D.circadian_disruption_score(duty, as_of),
        "days_in_high_risk_posting": E.days_in_high_risk_posting(deployments, as_of),
        "family_separation_index": E.family_separation_index(deployments, as_of),
        "deployment_count_12m": E.deployment_count_12m(deployments, as_of),
        "transfer_count_12m": C.transfer_count_12m(transfers, as_of),
        "promotion_board_pending": C.promotion_board_pending(career),
        "inquiry_court_pending": C.inquiry_court_pending(career),
        "inquiry_age_days": C.inquiry_age_days(career),
        "denied_training_count": C.denied_training_count(career),
        "sick_report_freq": H.sick_report_freq(medical, as_of),
        "pt_absence_unexplained": H.pt_absence_unexplained(medical, duty, as_of),
        "medical_visit_trend": H.medical_visit_trend(medical, as_of),
        "days_since_injury": H.days_since_injury(medical, as_of),
        "life_event_bereavement": T.gated_life_event("V1"),
        "life_event_marital_change": T.gated_life_event("V2"),
        "life_event_salary_advance": T.gated_life_event("V3"),
    }


ACTIVE_SIGNAL_KEYS = [
    "days_since_home_leave",
    "leave_cancel_count",
    "leave_denial_count",
    "early_return_days",
    "consecutive_duty_days",
    "night_shift_ratio",
    "rotation_speed_direction",
    "circadian_disruption_score",
    "days_in_high_risk_posting",
    "family_separation_index",
    "deployment_count_12m",
    "transfer_count_12m",
    "promotion_board_pending",
    "inquiry_court_pending",
    "inquiry_age_days",
    "denied_training_count",
    "sick_report_freq",
    "pt_absence_unexplained",
    "medical_visit_trend",
    "days_since_injury",
]


def snapshot_payload(values: dict[str, float | None]) -> dict[str, Any]:
    return {k: values.get(k) for k in ACTIVE_SIGNAL_KEYS}
