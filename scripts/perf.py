#!/usr/bin/env python3
"""TC-701 / TC-702 — the NFR-06 performance envelope, measured not asserted.

    python3 scripts/perf.py            # measure and print
    python3 scripts/perf.py --gate     # …and exit non-zero if a gate is missed

Gates (docs/quality/test-plan.md §6):
  TC-701  full 1,000-personnel signal + risk recompute        < 60 s
  TC-702  cold-start commander aggregate query, p95           < 2 s

The point of recording the machine alongside the number is that "12 s" means
nothing without it — the demo runs on a laptop, and the runbook needs to know
how much headroom that laptop has.
"""

from __future__ import annotations

import argparse
import os
import platform
import statistics
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, ROOT)

GATE_RECOMPUTE_S = 60.0
GATE_AGGREGATE_S = 2.0


def machine() -> str:
    bits = [platform.platform(), platform.processor() or platform.machine()]
    try:
        import subprocess

        brand = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], stderr=subprocess.DEVNULL
        )
        bits.append(brand.decode().strip())
    except Exception:
        pass
    bits.append("python " + platform.python_version())
    return " · ".join(b for b in bits if b)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true", help="exit non-zero if a gate is missed")
    parser.add_argument("--personnel", type=int, default=1000)
    args = parser.parse_args(argv)

    db_path = tempfile.mktemp(suffix=".db")
    url = "sqlite:///" + db_path

    from app.db import configure_engine, init_db, SessionLocal

    configure_engine(url)
    init_db()

    from app.clock import as_of, set_as_of
    from app.config import get_settings

    set_as_of(get_settings().as_of_date())

    from data.gen import main as generate

    t0 = time.perf_counter()
    rc = generate(
        ["--seed", "42", "--personnel", str(args.personnel), "--db-url", url, "--quiet"]
    )
    t_gen = time.perf_counter() - t0
    if rc != 0:
        print("generator failed", file=sys.stderr)
        return rc

    from app.risk.scorer import recompute_many
    from app.signals.snapshot import recompute_all

    db = SessionLocal()
    try:
        t0 = time.perf_counter()
        n_signals = len(recompute_all(db, as_of()))
        db.commit()
        t_signals = time.perf_counter() - t0

        t0 = time.perf_counter()
        n_risk = recompute_many(db, None, as_of=as_of())
        db.commit()
        t_risk = time.perf_counter() - t0

        from app.models import IdentityMap
        from app.privacy.kanonymity import aggregate_unit

        units = sorted({r.unit_id for r in db.query(IdentityMap).all()})
        samples = []
        for unit in units[:40]:
            t0 = time.perf_counter()
            aggregate_unit(db, unit)
            samples.append(time.perf_counter() - t0)
    finally:
        db.close()
        try:
            os.unlink(db_path)
        except OSError:
            pass

    total = t_signals + t_risk
    p95 = statistics.quantiles(samples, n=20)[-1] if len(samples) >= 20 else max(samples)

    print("machine: %s" % machine())
    print("fixture: seed 42 · %d personnel · 90 days" % args.personnel)
    print("  generate + write        %7.2f s" % t_gen)
    print("  signal recompute (%4d) %7.2f s" % (n_signals, t_signals))
    print("  risk recompute   (%4d) %7.2f s" % (n_risk, t_risk))
    print(
        "  TC-701 recompute total  %7.2f s   gate < %.0f s   %s"
        % (total, GATE_RECOMPUTE_S, "PASS" if total < GATE_RECOMPUTE_S else "FAIL")
    )
    print(
        "  TC-702 aggregate p95    %7.1f ms  gate < %.0f ms  %s"
        % (p95 * 1000, GATE_AGGREGATE_S * 1000, "PASS" if p95 < GATE_AGGREGATE_S else "FAIL")
    )

    if args.gate and (total >= GATE_RECOMPUTE_S or p95 >= GATE_AGGREGATE_S):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
