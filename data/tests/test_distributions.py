"""TC-503 — FK integrity and distributions inside the declared tolerances.

`Given a fresh database, when seeding runs, then all FK constraints pass and
aggregate distributions fall within neel's specified tolerances.`
(test-plan.md §3)

The tolerance table lives in ``data/spec.py::TOLERANCES`` and is reproduced in
``data/README.md``. Each entry is either ``declared`` (the target is a spec
constant, so the check proves the generator obeys its own config) or
``emergent`` (the target is the reference-run value, so the check is a
regression guard).
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from data import INGEST_DATASETS, TABLES
from data import spec as S
from data.gen import build
from data.validate import metrics, validate
from data.writer_csv import build_csv_noise

REFERENCE_N = 1000


@pytest.fixture(scope="module")
def reference():
    return build(seed=42, personnel=REFERENCE_N)


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------


def test_full_validation_passes(reference):
    report = validate(reference)
    assert report.ok, report.text()


def test_every_child_row_points_at_a_known_person(reference):
    people = set(row["pseudonym_id"] for row in reference.personnel)
    personnel_ids = set(row["personnel_id"] for row in reference.personnel)
    for table in ("leave", "roster", "deployment", "transfer", "training", "medical",
                  "career", "checkin", "instrument", "passive"):
        for row in reference.table(table):
            assert row["pseudonym_id"] in people, table
    for row in reference.consent:
        assert row["principal_pseudonym"] in people
    for table in ("leave", "roster", "deployment", "transfer", "medical", "career"):
        for row in reference.table(table):
            assert row["personnel_id"] in personnel_ids, table


def test_units_referenced_by_rosters_and_incidents_exist(reference):
    units = set(row["unit_id"] for row in reference.units)
    for row in reference.roster:
        assert row["unit_id"] in units
    for row in reference.incident:
        assert row["unit_id"] in units


def test_natural_keys_are_unique(reference):
    for table, key in (
        ("personnel", ("personnel_id",)),
        ("roster", ("pseudonym_id", "duty_date")),
        ("leave", ("pseudonym_id", "applied_at", "leave_type")),
        ("checkin", ("pseudonym_id", "recorded_at")),
        ("passive", ("pseudonym_id", "recorded_at")),
        ("instrument", ("pseudonym_id", "instrument", "recorded_at")),
        ("consent", ("principal_pseudonym", "bundle_id")),
        ("incident", ("incident_id",)),
    ):
        keys = [tuple(row[c] for c in key) for row in reference.table(table)]
        assert len(keys) == len(set(keys)), table


def test_pseudonym_and_personnel_namespaces_do_not_collide_with_backend_fixtures(reference):
    """kv's hand-written fixtures are CR-3BN-xx / CR-TINY-x / ps_3bnxx / ps_tinyx."""
    for row in reference.personnel:
        pid = row["personnel_id"]
        pseudo = row["pseudonym_id"]
        if pid == S.PERSONA_PERSONNEL_ID:
            continue
        assert pid.startswith("CR-GEN-"), pid
        assert pseudo.startswith("ps_gen"), pseudo
    for row in reference.incident:
        assert row["incident_id"] == S.PERSONA_INCIDENT_ID or row["incident_id"].startswith(
            "INC-GEN-"
        ), row["incident_id"]


# ---------------------------------------------------------------------------
# Distributions
# ---------------------------------------------------------------------------


def test_every_tolerance_is_measured(reference):
    measured = metrics(reference)
    for tol in S.TOLERANCES:
        assert tol.key in measured, tol.key


@pytest.mark.parametrize("tol", S.TOLERANCES, ids=lambda t: t.key)
def test_metric_inside_tolerance(reference, tol):
    value = metrics(reference)[tol.key]
    assert abs(value - tol.target) <= S.scaled_tolerance(tol, REFERENCE_N), (
        "{0}={1:.4f} target={2:.4f} +/- {3:.4f} ({4}, {5})".format(
            tol.key, value, tol.target, tol.abs_tol, tol.kind, tol.note)
    )


@pytest.mark.parametrize("seed", (7, 2026))
def test_tolerances_hold_for_other_seeds(seed):
    report = validate(build(seed=seed, personnel=400))
    assert report.ok, report.text()


def test_dates_never_leave_the_seed_anchored_window(reference):
    earliest = date.fromordinal(S.ARC_START.toordinal() - S.PRE_ARC_LOOKBACK_DAYS)
    latest = date.fromordinal(S.ARC_END.toordinal() + S.RAW_TTL_DAYS)
    for row in reference.roster:
        assert earliest <= date.fromisoformat(row["duty_date"]) <= latest
    for row in reference.consent:
        assert earliest <= datetime.fromisoformat(row["granted_at"]).date() <= latest


def test_non_participants_still_have_hr_and_passive_signals(reference):
    """F09: the dashboard must stay alive for people who never check in."""
    non_participants = set(
        row["pseudonym_id"] for row in reference.personnel if not row["participant"]
    )
    assert non_participants
    with_checkin = set(row["pseudonym_id"] for row in reference.checkin)
    with_roster = set(row["pseudonym_id"] for row in reference.roster)
    with_passive = set(row["pseudonym_id"] for row in reference.passive)
    with_consent = set(row["principal_pseudonym"] for row in reference.consent)
    assert not (non_participants & with_checkin)
    assert not (non_participants & with_consent)
    assert non_participants <= with_roster
    assert non_participants <= with_passive


def test_amber_cohort_exists_and_is_a_low_background_rate(reference):
    amber = [row for row in reference.personnel if row["cohort"] == S.COHORT_AMBER]
    assert amber, "there must be some naturally occurring amber trajectories"
    share = len(amber) / len(reference.personnel)
    assert 0.01 <= share <= 0.12, share


def test_silent_withdrawal_fixture_exists(reference):
    withdrawn = [row for row in reference.consent if row["withdrawn_at"]]
    assert withdrawn, "TC-407 needs at least one silent withdrawal"
    for row in withdrawn:
        last = max(
            (c["recorded_at"] for c in reference.checkin
             if c["pseudonym_id"] == row["principal_pseudonym"]),
            default=None,
        )
        if last is not None:
            assert date.fromisoformat(last) <= datetime.fromisoformat(
                row["withdrawn_at"]
            ).date()


def test_instrument_scores_stay_inside_their_published_ranges(reference):
    for row in reference.instrument:
        lo, hi = S.INSTRUMENT_SCORE_RANGE[row["instrument"]]
        assert lo <= row["score"] <= hi, row
        if row["instrument"] == "PHQ-9":
            assert row["item_9"] in (0, 1)
        else:
            assert row["item_9"] is None


def test_passive_rows_carry_derived_features_only(reference):
    allowed = set(S.PASSIVE_ALLOWED_FIELDS) | {"id"}
    for row in reference.passive[:500]:
        assert set(row.keys()) <= allowed
    for table in TABLES:
        rows = reference.table(table)
        if not rows:
            continue
        for column in rows[0]:
            for banned in S.FORBIDDEN_FIELD_SUBSTRINGS:
                assert banned not in column.lower(), "{0}.{1}".format(table, column)


# ---------------------------------------------------------------------------
# CSV contract
# ---------------------------------------------------------------------------


def test_csv_columns_match_the_backend_ingest_schemas(backend_ingest_schemas):
    assert set(backend_ingest_schemas.DATASETS) == set(INGEST_DATASETS)
    for dataset, model in backend_ingest_schemas.SCHEMA_BY_DATASET.items():
        assert tuple(model.model_fields.keys()) == S.INGEST_COLUMNS[dataset], dataset


def test_csv_noise_is_deterministic_and_within_rate(reference):
    again = build_csv_noise(reference, reference.seed)
    assert again == reference.csv_noise
    noisy_rows = sum(len(reference.table(name)) for name in S.CSV_NOISE_DATASETS)
    duplicates = [e for e in reference.csv_noise if e["kind"] == "duplicate"]
    malformed = [e for e in reference.csv_noise if e["kind"] == "malformed"]
    assert duplicates and malformed, "TC-102's rejection path must be exercised"
    assert abs(len(duplicates) / noisy_rows - S.CSV_DUPLICATE_RATE) < 0.004
    assert abs(len(malformed) / noisy_rows - S.CSV_MALFORMED_RATE) < 0.004


def test_csv_noise_never_reaches_the_db_payload(reference):
    """Noise is a CSV-only artefact; the upserted payload stays clean."""
    for entry in reference.csv_noise:
        if entry["kind"] != "malformed":
            continue
        assert entry["row"] not in reference.table(entry["dataset"])
