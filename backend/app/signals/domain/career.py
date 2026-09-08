from __future__ import annotations

from datetime import date, timedelta

from ..types import CareerRow, TransferRow


def transfer_count_12m(records: list[TransferRow], as_of: date) -> float:
    start = as_of - timedelta(days=365)
    return float(sum(1 for r in records if start <= r.effective_date <= as_of))


def promotion_board_pending(career: CareerRow | None) -> float | None:
    if career is None or career.promotion_board_pending_months is None:
        return None
    return float(career.promotion_board_pending_months)


def inquiry_court_pending(career: CareerRow | None) -> float | None:
    if career is None:
        return None
    return 1.0 if career.inquiry_court_pending else 0.0


def inquiry_age_days(career: CareerRow | None) -> float | None:
    if career is None or not career.inquiry_court_pending:
        return None
    if career.inquiry_age_days is None:
        return None
    return float(career.inquiry_age_days)


def denied_training_count(career: CareerRow | None) -> float | None:
    if career is None:
        return None
    return float(career.denied_training_count_12m)
