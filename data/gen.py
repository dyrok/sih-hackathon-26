"""``python -m data.gen`` — the F09 synthetic data generator CLI.

    python -m data.gen --seed 42 --personnel 1000
    python -m data.gen --seed 42 --personnel 1000 --format csv --out-dir DIR
    python -m data.gen --seed 42 --persona-only
    python -m data.gen --seed 42 --personnel 1000 --dry-run

Exits non-zero with a readable report on any validation failure (FK violation,
k < 5 unit, persona-arc mismatch, distribution outside tolerance).

Determinism: the same ``--seed`` produces a byte-identical payload, because
every random draw comes from a blake2b-derived per-stream RNG and every date
comes from the fixed epoch ``data.spec.ARC_START``. The generator never calls
``datetime.now()`` or ``date.today()`` for a data value.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List, Optional

from . import Dataset, TABLES, checksum
from . import persona as persona_mod
from . import spec as S
from .events import build_incidents, generate_person_hr
from .passive import build_passive, sleep_series
from .population import build_population
from .selfreport import generate_self_report
from .validate import Report, validate
from .writer_csv import build_csv_noise, write_csv

DEFAULT_SEED = 42
DEFAULT_PERSONNEL = 1000
DEFAULT_OUT_DIR = "out/saarthi-csv"


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


def build(
    seed: int = DEFAULT_SEED,
    personnel: int = DEFAULT_PERSONNEL,
    persona_only: bool = False,
    participation: float = S.PARTICIPATION_RATE_DEFAULT,
) -> Dataset:
    """Generate the complete payload in memory."""
    if persona_only:
        ds = persona_mod.build_persona()
        ds.seed = seed
        ds.personnel_requested = 1
        ds.persona_only = True
        ds.csv_noise = build_csv_noise(ds, seed)
        return ds

    population = build_population(seed, personnel, participation)
    ds = Dataset(seed=seed, personnel_requested=personnel, persona_only=False)
    ds.units = [unit.to_row() for unit in population.units]

    scripted = persona_mod.build_persona()
    for person in population.people:
        if person.cohort == S.COHORT_PERSONA:
            for name in TABLES:
                if name in ("units", "csv_noise"):
                    continue
                ds.table(name).extend(scripted.table(name))
            continue
        hr = generate_person_hr(seed, person)
        series = sleep_series(seed, person, hr.roster_by_day)
        consent, checkins, instruments = generate_self_report(seed, person, series)
        ds.personnel.append(person.to_row())
        ds.leave.extend(hr.leave)
        ds.roster.extend(hr.roster)
        ds.deployment.extend(hr.deployment)
        ds.transfer.extend(hr.transfer)
        ds.training.extend(hr.training)
        ds.medical.extend(hr.medical)
        ds.career.extend(hr.career)
        ds.consent.extend(consent)
        ds.checkin.extend(checkins)
        ds.instrument.extend(instruments)
        ds.passive.extend(build_passive(seed, person, series))

    ds.incident.extend(build_incidents(seed, population))
    ds.csv_noise = build_csv_noise(ds, seed)
    return ds


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def counts_text(ds: Dataset) -> str:
    counts = ds.counts()
    width = max(len(name) for name in counts)
    lines = ["rows:"]
    for name in TABLES:
        lines.append("  {0:<{1}}  {2:>8,}".format(name, width, counts[name]))
    lines.append("  {0:<{1}}  {2:>8,}".format("TOTAL", width, sum(counts.values())))
    return "\n".join(lines)


def header_text(ds: Dataset, participation: float, digest: str) -> str:
    return "\n".join(
        [
            "SAARTHI synthetic data generator v{0}  (F09 / QA-001 / QA-002)".format(
                S.GENERATOR_VERSION),
            "seed={0}  personnel={1}  participation={2:.2f}  persona_only={3}".format(
                ds.seed, ds.personnel_requested, participation, ds.persona_only),
            "epoch={0}..{1}  ({2} days, IST {3}, fixed offset, no DST)".format(
                S.ARC_START.isoformat(), S.ARC_END.isoformat(), S.ARC_DAYS, S.IST_LABEL),
            "payload sha256={0}".format(digest),
        ]
    )


def metrics_text(report: Report, personnel: int) -> str:
    if not report.metrics:
        return ""
    lines = ["distributions (target +/- tolerance, see data/spec.py TOLERANCES):"]
    targets = dict((t.key, t) for t in S.TOLERANCES)
    for key in sorted(report.metrics):
        tol = targets.get(key)
        if tol is None:
            lines.append("  {0:<42} {1:.4f}".format(key, report.metrics[key]))
        else:
            lines.append("  {0:<42} {1:.4f}   (target {2:.4f} +/- {3:.4f}, {4})".format(
                key, report.metrics[key], tol.target,
                S.scaled_tolerance(tol, personnel), tol.kind))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m data.gen",
        description="SAARTHI synthetic data generator (F09). Deterministic, "
                    "seed-anchored, k>=5 by construction.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="master seed (default: %(default)s)")
    parser.add_argument("--personnel", type=int, default=DEFAULT_PERSONNEL,
                        help="population size (default: %(default)s)")
    parser.add_argument("--persona-only", action="store_true",
                        help="generate DEMO-PERSONA-01 only (fast demo re-seed)")
    parser.add_argument("--format", choices=("db", "csv"), default="db",
                        help="output target (default: %(default)s)")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR,
                        help="CSV output directory (default: %(default)s)")
    parser.add_argument("--db-url", default=None,
                        help="SQLAlchemy URL (default: the backend's sqlite database, "
                             "or $SAARTHI_DATABASE_URL)")
    parser.add_argument("--participation", type=float, default=S.PARTICIPATION_RATE_DEFAULT,
                        help="voluntary check-in participation rate (default: %(default)s)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the persona arc table and row counts; write nothing")
    parser.add_argument("--quiet", action="store_true",
                        help="suppress the run summary; errors still print to stderr")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not 0.0 <= args.participation <= 1.0:
        print("--participation must be between 0 and 1", file=sys.stderr)
        return 2
    if args.personnel < 1 and not args.persona_only:
        print("--personnel must be >= 1", file=sys.stderr)
        return 2

    ds = build(
        seed=args.seed,
        personnel=args.personnel,
        persona_only=args.persona_only,
        participation=args.participation,
    )
    digest = checksum(ds)
    report = validate(ds)

    out: List[str] = [
        header_text(ds, args.participation, digest),
        "",
        persona_mod.arc_table_text(),
        "",
        counts_text(ds),
        "",
        report.text(),
    ]
    metrics_block = metrics_text(report, len(ds.personnel))
    if metrics_block:
        out.extend(["", metrics_block])

    if not report.ok:
        print("\n".join(out), file=sys.stderr)
        print("\nFAILED: {0} validation check(s) failed; nothing was written.".format(
            len(report.failures())), file=sys.stderr)
        return 1

    if args.dry_run:
        out.append("")
        out.append("--dry-run: nothing written.")
    elif args.format == "csv":
        manifest = write_csv(ds, args.out_dir, payload_checksum=digest)
        out.append("")
        out.append("wrote {0} files to {1}".format(len(manifest["files"]), args.out_dir))
        for entry in manifest["files"]:
            out.append("  {0:<18} {1:>8,} rows  {2}  {3}".format(
                entry["file"], entry["rows"], entry["contract"], entry["sha256"][:12]))
    else:
        from .writer_db import default_db_url, write_db

        url = args.db_url or default_db_url()
        written = write_db(ds, url)
        out.append("")
        out.append("upserted into {0}".format(url))
        for table in TABLES:
            stats = written.get(table)
            if stats:
                out.append("  {0:<14} +{1:,} inserted  ~{2:,} updated".format(
                    table, stats["inserted"], stats["updated"]))
        out.append("")
        out.append("next: cd backend && .venv/bin/python -m app.seed   "
                   "# users, signals recompute, scoring")

    if not args.quiet:
        print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
