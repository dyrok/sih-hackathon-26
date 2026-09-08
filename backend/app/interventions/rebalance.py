from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..models import HrDutyRoster, HrLeaveRecord, IdentityMap, SignalSnapshot


def _load(db: Session, pid: str, as_of: date) -> float:
    snap = (
        db.query(SignalSnapshot)
        .filter(
            SignalSnapshot.pseudonym_id == pid,
            SignalSnapshot.signal_key == "consecutive_duty_days",
            SignalSnapshot.window_end == as_of,
        )
        .one_or_none()
    )
    nights = (
        db.query(SignalSnapshot)
        .filter(
            SignalSnapshot.pseudonym_id == pid,
            SignalSnapshot.signal_key == "night_shift_ratio",
            SignalSnapshot.window_end == as_of,
        )
        .one_or_none()
    )
    sep = (
        db.query(SignalSnapshot)
        .filter(
            SignalSnapshot.pseudonym_id == pid,
            SignalSnapshot.signal_key == "family_separation_index",
            SignalSnapshot.window_end == as_of,
        )
        .one_or_none()
    )
    duty = float(snap.value or 0) if snap else 0.0
    night = float(nights.value or 0) if nights else 0.0
    return duty + 8.0 * night + (0.0)  # welfare weights applied only in welfare_weighted


def _on_leave(db: Session, pid: str, day: date) -> bool:
    rows = db.query(HrLeaveRecord).filter(HrLeaveRecord.pseudonym_id == pid).all()
    for r in rows:
        if r.cancelled_at is not None or r.denial_reason:
            continue
        if r.sanctioned_from and r.sanctioned_to and r.sanctioned_from <= day <= r.sanctioned_to:
            return True
    return False


def greedy_rebalance(
    db: Session,
    *,
    unit_id: str,
    mode: str,
    as_of: date,
    horizon_days: int = 14,
) -> dict[str, Any]:
    people = db.query(IdentityMap).filter(IdentityMap.unit_id == unit_id).all()
    pids = [p.pseudonym_id for p in people]
    ranks = {p.pseudonym_id: p.rank for p in people}
    start = as_of
    end = as_of + timedelta(days=horizon_days - 1)
    slots = (
        db.query(HrDutyRoster)
        .filter(
            HrDutyRoster.unit_id == unit_id,
            HrDutyRoster.duty_date >= start,
            HrDutyRoster.duty_date <= end,
            HrDutyRoster.rest_day.is_(False),
        )
        .all()
    )
    loads: dict[str, float] = {pid: _load(db, pid, as_of) for pid in pids}
    if mode == "welfare_weighted":
        from ..models import RiskScore

        for pid in pids:
            rs = (
                db.query(RiskScore)
                .filter(RiskScore.pseudonym_id == pid)
                .order_by(RiskScore.computed_at.desc())
                .first()
            )
            bump = {"green": 0, "amber": 4, "red": 8, "critical": 12}.get(rs.tier if rs else "green", 0)
            loads[pid] += bump

    max_before = max(loads.values()) if loads else 0.0
    swaps: list[dict[str, str]] = []
    infeasible: list[dict[str, str]] = []

    # Greedy: repeatedly move a shift from the most-loaded to the least-loaded qualified person.
    by_person: dict[str, list[HrDutyRoster]] = {pid: [] for pid in pids}
    for s in slots:
        by_person.setdefault(s.pseudonym_id, []).append(s)

    for _ in range(min(40, len(slots))):
        if not loads:
            break
        heavy = max(loads, key=lambda k: loads[k])
        light = min(loads, key=lambda k: loads[k])
        if loads[heavy] - loads[light] < 1.0:
            break
        moved = False
        for slot in list(by_person.get(heavy, [])):
            if _on_leave(db, light, slot.duty_date):
                continue
            if ranks.get(heavy) != ranks.get(light) and ranks.get(light) not in {
                "Constable",
                "Head Constable",
                "ASI",
                "SI",
                "Inspector",
            }:
                continue
            # don't double-book light
            if any(s.duty_date == slot.duty_date and not s.rest_day for s in by_person.get(light, [])):
                continue
            swaps.append(
                {
                    "from": heavy,
                    "to": light,
                    "shift": f"{slot.duty_date.isoformat()}:{slot.shift_code}",
                }
            )
            by_person[heavy].remove(slot)
            by_person.setdefault(light, []).append(slot)
            loads[heavy] -= 1
            loads[light] += 1
            moved = True
            break
        if not moved:
            infeasible.append({"person": heavy, "reason": "no_eligible_swap"})
            break

    max_after = max(loads.values()) if loads else 0.0
    return {
        "swaps": swaps,
        "max_load_before": max_before,
        "max_load_after": max_after,
        "infeasible_shifts": infeasible,
        "loads": {k: v for k, v in loads.items()} if mode != "workload" else None,
    }
