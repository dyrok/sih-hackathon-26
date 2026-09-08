from __future__ import annotations

from datetime import date, timedelta


def mean(xs: list[float]) -> float | None:
    if not xs:
        return None
    return sum(xs) / len(xs)


def deviation_from_baseline(current: float | None, baseline: float | None) -> float | None:
    if current is None or baseline is None or baseline == 0:
        return None
    return (current - baseline) / abs(baseline)


def cusum_change_point(values: list[tuple[date, float]], threshold: float = 4.0, drift: float = 0.25) -> date | None:
    """Lightweight CUSUM (stdlib). Returns the date of a sustained mean shift, if any."""
    if len(values) < 8:
        return None
    xs = [v for _, v in values]
    mu = sum(xs) / len(xs)
    gp = gn = 0.0
    for d, x in values:
        gp = max(0.0, gp + (x - mu - drift))
        gn = min(0.0, gn + (x - mu + drift))
        if gp > threshold or gn < -threshold:
            return d
    return None


def sleep_baseline_and_dev(
    series: list[tuple[date, float]],
    as_of: date,
    window_days: int = 60,
    recent_days: int = 7,
    min_history_days: int = 14,
) -> tuple[float | None, float | None, date | None, int]:
    start = as_of - timedelta(days=window_days - 1)
    recent_start = as_of - timedelta(days=recent_days - 1)
    hist = [(d, v) for d, v in series if start <= d < recent_start]
    recent = [(d, v) for d, v in series if recent_start <= d <= as_of]
    history_days = len({d for d, _ in hist})
    base = mean([v for _, v in hist])
    cur = mean([v for _, v in recent])
    dev = deviation_from_baseline(cur, base)
    cp = cusum_change_point(hist + recent)
    if history_days < min_history_days:
        return base, None, cp, history_days
    return base, dev, cp, history_days
