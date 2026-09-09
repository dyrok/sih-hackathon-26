"""``python -m data`` is an alias for ``python -m data.gen``."""

from __future__ import annotations

from .gen import main

if __name__ == "__main__":
    raise SystemExit(main())
