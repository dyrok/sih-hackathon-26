"""CSV export for the backend ingest path (TC-101/TC-102).

The seven ingest datasets are written with **exactly** the columns
``backend/app/ingest/schemas.py`` declares, in declaration order, so
``POST /ingest/hr/{dataset}`` accepts them without a mapping layer. Additional
reference CSVs (personnel, units, training, consent, check-ins, instruments,
passive) are written alongside and are explicitly *not* part of that contract.

Realism noise (F09): a small, seeded share of rows is re-emitted verbatim or
emitted broken. That is deliberate — F01's rejection path is *tested*, not
bypassed, so the demo shows a non-zero quarantine count with row-level reasons.
Noise lives in the payload (``Dataset.csv_noise``) rather than being invented at
write time, so it is covered by the TC-501 checksum and never touches the DB
writer.

Every file is written with LF line endings and UTF-8, so two runs of the same
seed produce byte-identical files on any platform.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from . import Dataset, INGEST_DATASETS, rng_for
from . import spec as S


def build_csv_noise(ds: Dataset, seed: int) -> List[Dict[str, Any]]:
    """Deterministic duplicate/malformed rows, one pass per noisy dataset."""
    noise: List[Dict[str, Any]] = []
    for dataset in S.CSV_NOISE_DATASETS:
        rows = ds.table(dataset)
        if not rows:
            continue
        rng = rng_for(seed, "csv_noise", dataset)
        for index in range(len(rows)):
            roll = rng.random()
            if roll < S.CSV_DUPLICATE_RATE:
                noise.append(
                    {
                        "dataset": dataset,
                        "kind": "duplicate",
                        "malform": None,
                        "after_index": index,
                        "row": dict(rows[index]),
                    }
                )
            elif roll < S.CSV_DUPLICATE_RATE + S.CSV_MALFORMED_RATE:
                kind = S.CSV_MALFORM_KINDS[rng.randrange(len(S.CSV_MALFORM_KINDS))]
                noise.append(
                    {
                        "dataset": dataset,
                        "kind": "malformed",
                        "malform": kind,
                        "after_index": index,
                        "row": _malform(dict(rows[index]), dataset, kind),
                    }
                )
    return noise


def _malform(row: Dict[str, Any], dataset: str, kind: str) -> Dict[str, Any]:
    column = S.REQUIRED_DATE_COLUMN.get(dataset)
    if kind == "blank_required_date" and column:
        row[column] = ""
    elif kind == "bad_date_format" and column:
        row[column] = S.CSV_BAD_DATE_LITERAL
    elif kind == "unknown_personnel_id":
        row["personnel_id"] = S.CSV_UNKNOWN_PERSONNEL_ID
    return row


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def _write(path: str, columns, rows) -> int:
    n = 0
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator=S.CSV_LINE_TERMINATOR)
        writer.writerow(list(columns))
        for row in rows:
            writer.writerow([_cell(row.get(col)) for col in columns])
            n += 1
    return n


def _noise_by_dataset(ds: Dataset) -> Dict[str, Dict[int, List[Dict[str, Any]]]]:
    out: Dict[str, Dict[int, List[Dict[str, Any]]]] = {}
    for entry in ds.csv_noise:
        bucket = out.setdefault(entry["dataset"], {})
        bucket.setdefault(entry["after_index"], []).append(entry)
    return out


def _rows_with_noise(ds: Dataset, dataset: str, noise) -> List[Dict[str, Any]]:
    rows = ds.table(dataset)
    injected = noise.get(dataset, {})
    if not injected:
        return rows
    out: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        out.append(row)
        for entry in injected.get(index, []):
            out.append(entry["row"])
    return out


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(ds: Dataset, out_dir: str, payload_checksum: Optional[str] = None) -> Dict[str, Any]:
    """Write every CSV plus a manifest. Returns the manifest dict."""
    os.makedirs(out_dir, exist_ok=True)
    noise = _noise_by_dataset(ds)
    files: List[Dict[str, Any]] = []

    for dataset in INGEST_DATASETS:
        path = os.path.join(out_dir, "{0}.csv".format(dataset))
        rows = _rows_with_noise(ds, dataset, noise)
        written = _write(path, S.INGEST_COLUMNS[dataset], rows)
        files.append(
            {
                "file": "{0}.csv".format(dataset),
                "dataset": dataset,
                "contract": "ingest",
                "rows": written,
                "clean_rows": len(ds.table(dataset)),
                "sha256": sha256_file(path),
            }
        )

    for name, columns in sorted(S.REFERENCE_COLUMNS.items()):
        path = os.path.join(out_dir, "{0}.csv".format(name))
        written = _write(path, columns, ds.table(name))
        files.append(
            {
                "file": "{0}.csv".format(name),
                "dataset": name,
                "contract": "reference",
                "rows": written,
                "clean_rows": written,
                "sha256": sha256_file(path),
            }
        )

    manifest = {
        "generator": "data.gen",
        "generator_version": S.GENERATOR_VERSION,
        "seed": ds.seed,
        "personnel_requested": ds.personnel_requested,
        "persona_only": ds.persona_only,
        "arc_start": S.ARC_START.isoformat(),
        "arc_end": S.ARC_END.isoformat(),
        "timezone": "IST {0} (fixed offset, no DST)".format(S.IST_LABEL),
        "payload_checksum": payload_checksum,
        "counts": ds.counts(),
        "csv_noise": {
            "duplicate": sum(1 for e in ds.csv_noise if e["kind"] == "duplicate"),
            "malformed": sum(1 for e in ds.csv_noise if e["kind"] == "malformed"),
        },
        "files": files,
    }
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True))
        handle.write("\n")
    return manifest
