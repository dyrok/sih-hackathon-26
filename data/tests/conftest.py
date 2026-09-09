"""Make ``data`` importable from the repo root, and offer the backend lazily.

``python -m pytest data/tests`` from the repo root already puts the CWD on
``sys.path``; this belt-and-braces insert means the suite also runs from any
other working directory (``pytest /path/to/repo/data/tests``).
"""

from __future__ import annotations

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")

for path in (REPO_ROOT, BACKEND_ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def backend_seed():
    """kv's demo seed module, or a skip if the backend is not importable."""
    try:
        from app import seed  # noqa: WPS433
    except Exception as exc:                                  # pragma: no cover
        pytest.skip("backend not importable ({0})".format(exc))
    return seed


@pytest.fixture(scope="session")
def backend_ingest_schemas():
    """The backend's ingest pydantic schemas, or a skip."""
    try:
        from app.ingest import schemas  # noqa: WPS433
    except Exception as exc:                                  # pragma: no cover
        pytest.skip("backend not importable ({0})".format(exc))
    return schemas
