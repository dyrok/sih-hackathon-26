"""TC-501 — same seed, byte-identical output.

`Given --seed 42 --personnel 1000, when generation runs twice, then outputs are
byte-identical (checksum match).`  (test-plan.md §3)

The suite proves three separate things, because "deterministic" quietly means
all three:

1. the payload checksum matches across two independent builds;
2. the CSV files match byte for byte (line endings, float formatting, row order);
3. changing one parameter does not reshuffle the streams it should not touch.

Plus a source-level guard: nothing in ``data/`` may read the wall clock.
"""

from __future__ import annotations

import ast
import os

from data import TABLES, canonical, checksum
from data.gen import build
from data.writer_csv import sha256_file, write_csv

SEED = 42
FULL_N = 1000
SMALL_N = 120


def test_same_seed_same_checksum():
    first = build(seed=SEED, personnel=FULL_N)
    second = build(seed=SEED, personnel=FULL_N)
    assert checksum(first) == checksum(second)
    assert first.counts() == second.counts()


def test_same_seed_row_for_row_identical():
    first = build(seed=SEED, personnel=SMALL_N)
    second = build(seed=SEED, personnel=SMALL_N)
    for table in TABLES:
        rows_a = first.table(table)
        rows_b = second.table(table)
        assert len(rows_a) == len(rows_b), table
        for index, (row_a, row_b) in enumerate(zip(rows_a, rows_b)):
            assert canonical(row_a) == canonical(row_b), "{0}[{1}]".format(table, index)


def test_different_seed_differs():
    assert checksum(build(seed=SEED, personnel=SMALL_N)) != checksum(
        build(seed=SEED + 1, personnel=SMALL_N)
    )


def test_persona_is_seed_independent():
    """The scripted arc is deterministic *and* identical for every seed.

    Only ``csv_noise`` differs — it is a seeded property of the export, not of
    the arc.
    """
    a = build(seed=SEED, persona_only=True)
    b = build(seed=SEED + 7, persona_only=True)
    for table in TABLES:
        if table == "csv_noise":
            continue
        assert [canonical(r) for r in a.table(table)] == [
            canonical(r) for r in b.table(table)
        ], table


def test_csv_export_is_byte_identical(tmp_path):
    ds = build(seed=SEED, personnel=SMALL_N)
    dir_a = str(tmp_path / "a")
    dir_b = str(tmp_path / "b")
    manifest_a = write_csv(build(seed=SEED, personnel=SMALL_N), dir_a)
    manifest_b = write_csv(ds, dir_b)
    names_a = sorted(entry["file"] for entry in manifest_a["files"])
    assert names_a == sorted(entry["file"] for entry in manifest_b["files"])
    for name in names_a:
        assert sha256_file(os.path.join(dir_a, name)) == sha256_file(
            os.path.join(dir_b, name)
        ), name


def test_new_parameter_does_not_reshuffle_other_streams():
    """Changing --participation must not move anybody's HR history.

    Per-personnel RNG streams are namespaced by purpose, so the roster / leave /
    deployment / medical / career streams are untouched by a self-report knob.
    """
    base = build(seed=SEED, personnel=SMALL_N, participation=0.35)
    other = build(seed=SEED, personnel=SMALL_N, participation=0.90)
    for table in ("roster", "leave", "deployment", "transfer", "medical", "career",
                  "training", "passive", "incident", "units"):
        assert [canonical(r) for r in base.table(table)] == [
            canonical(r) for r in other.table(table)
        ], table
    # ...while the self-report volume really did change.
    assert len(other.checkin) > len(base.checkin)


def test_no_wall_clock_in_generator_sources():
    """F09: dates come from a seed-anchored epoch, never wall-clock time.

    Parsed with ``ast`` rather than grepped, so prose about ``datetime.now()``
    in a docstring does not trip the guard and an actual call cannot hide in a
    string.
    """
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    banned_attrs = {"now", "today", "utcnow", "fromtimestamp"}
    offenders = []
    for name in sorted(os.listdir(package_dir)):
        if not name.endswith(".py"):
            continue
        path = os.path.join(package_dir, name)
        with open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            attr = node.func.attr
            base = getattr(node.func.value, "id", None)
            if attr in banned_attrs or (attr == "time" and base == "time"):
                offenders.append("{0}: {1}.{2}()".format(name, base, attr))
    assert not offenders, "wall-clock call in generator source: {0}".format(offenders)
