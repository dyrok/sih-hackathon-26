"""TC-504 — no emitted unit ever holds fewer than 5 personnel.

`Given the commander dashboard on seeded data, when aggregates render, then no
visible cell has < 5 contributors.`  (test-plan.md §3, ADR-0003)

The generator enforces k >= 5 *structurally*: the allocator reduces the number
of sub-units rather than creating an undersized one, so there is no draw that
can produce a 4-person platoon. The negative test forces one past the allocator
and proves the validator refuses to ship it.
"""

from __future__ import annotations

import pytest

from data import Dataset
from data import spec as S
from data.gen import build, main
from data.population import allocate, build_population, build_population_from_sizes, split_headcount
from data.validate import check_k_anonymity, validate, Report

SIZES = (25, 60, 61, 99, 120, 300, 512, 1000, 1001, 2000)


def _check(ds):
    report = Report()
    check_k_anonymity(ds, report)
    return report.checks[0]


# ---------------------------------------------------------------------------
# The allocator cannot produce an undersized unit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("total", SIZES)
def test_allocator_never_emits_a_unit_below_k(total):
    allocation = allocate(total)
    assert sum(size for _, _, _, size in allocation) == total
    for _, _, platoon_id, size in allocation:
        assert size >= S.K_ANONYMITY, "{0} has {1}".format(platoon_id, size)
    for level in (0, 1):
        totals = {}
        for row in allocation:
            totals[row[level]] = totals.get(row[level], 0) + row[3]
        for unit_id, size in totals.items():
            assert size >= S.K_ANONYMITY, "{0} has {1}".format(unit_id, size)


def test_split_headcount_drops_parts_instead_of_shrinking_them():
    assert split_headcount(12, 5, 25) == [12]              # cannot make 5 -> make 1
    assert split_headcount(12, 3, 5) == [6, 6]             # 3 parts would be 4 each
    assert min(split_headcount(1000, 5, 60)) >= 60
    assert split_headcount(0, 3, 5) == []


def test_split_headcount_respects_min_size():
    for total in range(5, 200):
        parts = split_headcount(total, 3, 5)
        assert sum(parts) == total
        assert min(parts) >= 5


@pytest.mark.parametrize("total", (60, 120, 400, 1000))
def test_generated_population_passes_the_k_guard(total):
    ds = build(seed=42, personnel=total)
    check = _check(ds)
    assert check.ok, check.detail
    counts = {}
    for row in ds.personnel:
        for level in ("battalion_id", "company_id", "platoon_id"):
            counts[row[level]] = counts.get(row[level], 0) + 1
    assert min(counts.values()) >= S.K_ANONYMITY


def test_units_table_agrees_with_actual_membership():
    ds = build(seed=42, personnel=400)
    declared = dict((u["unit_id"], u["size"]) for u in ds.units)
    actual = {}
    for row in ds.personnel:
        for level in ("battalion_id", "company_id", "platoon_id"):
            actual[row[level]] = actual.get(row[level], 0) + 1
    assert declared == actual


# ---------------------------------------------------------------------------
# Negative test — a forced 4-person unit must be refused
# ---------------------------------------------------------------------------


def _dataset_from(population):
    ds = Dataset(seed=42, personnel_requested=len(population.people))
    ds.personnel = [p.to_row() for p in population.people]
    ds.units = [u.to_row() for u in population.units]
    return ds


def test_forced_four_person_unit_is_refused():
    sizes = (
        ("9BN", "9BN-A", "9BN-A1", 20),
        ("9BN", "9BN-A", "9BN-A2", 4),        # <-- illegal
    )
    ds = _dataset_from(build_population_from_sizes(42, sizes))
    check = _check(ds)
    assert not check.ok
    assert "9BN-A2" in check.detail
    assert "k=5" in check.detail
    assert not validate(ds).ok


def test_forced_four_person_battalion_is_refused():
    sizes = (("9BN", "9BN-A", "9BN-A1", 4),)
    ds = _dataset_from(build_population_from_sizes(42, sizes))
    check = _check(ds)
    assert not check.ok
    assert "9BN" in check.detail


def test_declared_size_mismatch_is_refused():
    population = build_population(42, 60)
    ds = _dataset_from(population)
    ds.personnel = ds.personnel[:-1]                       # a body goes missing
    check = _check(ds)
    assert not check.ok
    assert "holds" in check.detail


def test_cli_exits_non_zero_when_the_k_guard_fails(monkeypatch, capsys):
    """The whole CLI must refuse, not just the checker."""
    monkeypatch.setattr(S, "K_ANONYMITY", 10 ** 6)
    code = main(["--seed", "42", "--personnel", "60", "--dry-run"])
    captured = capsys.readouterr()
    assert code == 1
    assert "FAILED" in captured.err
    assert "k_anonymity" in captured.err


def test_persona_only_skips_the_k_guard_explicitly():
    """A persona-only re-seed does not materialise unit membership; say so."""
    ds = build(seed=42, persona_only=True)
    check = _check(ds)
    assert check.ok and check.skipped
    assert "persona-only" in check.detail
