# SAARTHI backend (kv)

FastAPI + SQLAlchemy core API. Implements BACK-001…009: JWT/RBAC, append-only audit, HR ingest + 20 signals, rules engine v1, intervention ladder, k-anonymity aggregates, dual-key unmask, who-viewed-my-data.

Default store is SQLite (air-gap / laptop demo). Set `SAARTHI_DATABASE_URL` to a Postgres URL for the production shape (ADR-0006).

## Run

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed                 # demo users + DEMO-PERSONA-01
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs. Demo password for every seed user: `saarthi`.

| username | role |
|---|---|
| `jawan.demo` | jawan (Constable, 34, 3rd Bn) |
| `counsellor.a` | counsellor |
| `welfare.a` | welfare officer |
| `commander.3bn` | commander (aggregates only) |
| `admin` | admin (no individual read grant) |
| `auditor` | auditor (events, not content) |
| `hr.ingest` | HR ingest service account |

## Tests

```bash
cd backend
pytest -q
python -m app.ml.harness           # ML-002 persona arc + threshold sweep
```

## Firewall (ADR-0003)

A commander JWT is refused at middleware **and** at every individual handler. There is no `/welfare/personnel/{id}` data path — the route exists as a trap and always 403s. Unit aggregates suppress any cell with k < 5, including the complement.

## Clock

Demo `as_of` is `2026-09-01` (day 90 of the scripted persona). Tests inject the clock via `app.clock.set_as_of`.
