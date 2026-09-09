"""SAARTHI synthetic data generator (F09 / QA-001 / QA-002).

Owner: neel. Spec: ``docs/features/F09-synthetic-data-generator.md``.

This package holds the determinism primitives shared by every other module:

* :func:`stable_seed` / :func:`rng_for` — per-stream RNG derived from the master
  seed with a **stable** hash (blake2b of a string). Python's built-in ``hash()``
  is salted per process and is never used here.
* :func:`did` — deterministic row ids shaped like the backend's ``nid()``
  (``prefix_<12 hex>``) but reproducible across runs and machines.
* :class:`Dataset` — the in-memory payload every writer consumes.
* :func:`checksum` — streaming SHA-256 over the canonical payload (TC-501).

Nothing in this package reads the wall clock. All dates derive from
``data.spec.ARC_START``.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Iterable, List

__version__ = "1.0.0"

#: Logical tables in payload order. Order is part of the checksum contract.
TABLES = (
    "personnel",
    "units",
    "leave",
    "roster",
    "deployment",
    "transfer",
    "training",
    "incident",
    "medical",
    "career",
    "consent",
    "checkin",
    "instrument",
    "passive",
    "csv_noise",
)

#: The seven datasets the backend ingest path accepts
#: (``backend/app/ingest/schemas.py``: ``DATASETS``).
INGEST_DATASETS = ("leave", "roster", "deployment", "transfer", "incident", "medical", "career")


def stable_seed(*parts: Any) -> int:
    """A process-stable 64-bit seed from arbitrary parts.

    Uses blake2b over the ``|``-joined string form — never ``hash()``, which is
    salted per process and would break TC-501 across runs.
    """
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "big")


def rng_for(*parts: Any) -> random.Random:
    """A dedicated deterministic RNG stream for ``parts``.

    Streams are namespaced (``master_seed``, stream name, pseudonym, ...) so
    adding a parameter to one stream never reshuffles anybody else.
    """
    return random.Random(stable_seed(*parts))


def did(prefix: str, *parts: Any) -> str:
    """Deterministic row id shaped like the backend's ``nid()``."""
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return "{0}_{1}".format(prefix, hashlib.blake2b(key, digest_size=6).hexdigest())


def canonical(value: Any) -> str:
    """Canonical JSON for one row (sorted keys, no whitespace drift)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass
class Dataset:
    """The complete generated payload.

    Every list holds plain dicts so the payload is trivially canonicalisable,
    diffable and CSV-writable. Row order is deterministic and part of the
    TC-501 checksum.
    """

    seed: int = 0
    personnel_requested: int = 0
    persona_only: bool = False
    personnel: List[Dict[str, Any]] = field(default_factory=list)
    units: List[Dict[str, Any]] = field(default_factory=list)
    leave: List[Dict[str, Any]] = field(default_factory=list)
    roster: List[Dict[str, Any]] = field(default_factory=list)
    deployment: List[Dict[str, Any]] = field(default_factory=list)
    transfer: List[Dict[str, Any]] = field(default_factory=list)
    training: List[Dict[str, Any]] = field(default_factory=list)
    incident: List[Dict[str, Any]] = field(default_factory=list)
    medical: List[Dict[str, Any]] = field(default_factory=list)
    career: List[Dict[str, Any]] = field(default_factory=list)
    consent: List[Dict[str, Any]] = field(default_factory=list)
    checkin: List[Dict[str, Any]] = field(default_factory=list)
    instrument: List[Dict[str, Any]] = field(default_factory=list)
    passive: List[Dict[str, Any]] = field(default_factory=list)
    csv_noise: List[Dict[str, Any]] = field(default_factory=list)

    def table(self, name: str) -> List[Dict[str, Any]]:
        return getattr(self, name)

    def counts(self) -> Dict[str, int]:
        return dict((name, len(self.table(name))) for name in TABLES)

    def extend(self, other: "Dataset") -> None:
        for name in TABLES:
            self.table(name).extend(other.table(name))

    def field_names(self) -> Iterable[str]:
        return (f.name for f in fields(self))


def checksum(dataset: Dataset) -> str:
    """Streaming SHA-256 over the canonical payload (TC-501).

    Streaming keeps a 1,000-personnel payload (~200k rows) off the heap as one
    giant string while still hashing every byte of every row.
    """
    h = hashlib.sha256()
    h.update(canonical({"seed": dataset.seed, "n": dataset.personnel_requested,
                        "persona_only": dataset.persona_only,
                        "version": __version__}).encode("utf-8"))
    for name in TABLES:
        h.update(b"\x1e")
        h.update(name.encode("utf-8"))
        for row in dataset.table(name):
            h.update(b"\x1f")
            h.update(canonical(row).encode("utf-8"))
    return h.hexdigest()
