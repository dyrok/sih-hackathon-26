# SAARTHI — SIH 2026 · PS 26186

**AI-Based Predictive Personnel Stress & Welfare Monitoring System for Uniformed Forces**
Working name **SAARTHI** (सारथी — the charioteer who guides). Problem: [SIH 26186](https://sih2026.vuce.in/ps/SIH26186) · CRPF / Ministry of Home Affairs · MedTech/HealthTech.

> **Welfare, not discipline.** SAARTHI detects stress risk early from HR signals, voluntary check-ins and passive wellness data — and routes help (counsellor, roster change, Tele-MANAS) before crisis. Individual scores are architecturally incapable of reaching appraisal, promotion or posting decisions.

## Repo layout

- **[`docs/`](docs/README.md) — THE BRAIN.** Product, architecture, per-feature specs, compliance, explanations, quality.
- **[`executable/`](executable/README.md) — THE HANDS.** Per-member plans, AI-agent execution prompts, task board, rules.
- **[`backend/`](backend/README.md) — THE CORE API.** FastAPI: ingest, rules engine, interventions, k-anonymity, dual-key unmask.
- **[`web/`](web/README.md) — THE THREE SURFACES.** Next.js monorepo: jawan PWA (offline-first), counsellor console, commander dashboard.
- **[`data/`](data/README.md) — THE FIXTURE.** Deterministic synthetic population: 1,000 personnel x 90 days, one seed, one truth for tests, demo and model evaluation.
- [`AGENTS.md`](AGENTS.md) — rules every AI agent (and human) working here must follow.

## Run the prototype

One command sets everything up; `make` on its own lists the rest.

```bash
make setup          # backend venv + bun workspace
make seed           # demo persona (Constable, 34, 3rd Bn) + unit background
make api            # Core API        http://127.0.0.1:8000/docs
make jawan          # jawan PWA       http://localhost:3100
make counsellor     # counsellor console  http://localhost:3200
make commander      # commander dashboard http://localhost:3300
make demo           # the demo checklist, in running order
```

Every demo user's password is `saarthi`:

| username | role | what they see |
|---|---|---|
| `jawan.demo` | jawan | roster, 10-second check-in, own trend, consent, who-viewed-my-data |
| `counsellor.a` | counsellor | ranked case queue, evidence, dual-key unmask, notes, outcomes |
| `welfare.a` | welfare officer | assigned cases, the second unmask key, roster rebalancing |
| `commander.3bn` | commander | unit aggregates only — heatmap, morale, indicators, what-if, forecast |
| `admin` · `auditor` · `hr.ingest` | pipeline roles | no individual read grant between them |

A commander asking for one person gets **403 and an audit row the jawan can
read back**. That is the demo, and `make test` proves it 257 times.

```bash
make generate       # 1,000 personnel x 90 days of deterministic synthetic data
make test           # backend + generator + web suites
make check          # everything CI runs: boundaries, types, tests, build
make perf           # the NFR-06 performance envelope
```

## Team

| Member | Role |
|---|---|
| kv | Project Manager, Maintainer (merges all PRs) + co-backbone: engines, architecture, privacy law |
| neel | co-backbone (equal split): apps, dashboards, design, security model, RBAC, test plan, synthetic data |
| ayush | ML research assistant (1st year · simple guided tasks) |
| manan | Compliance research assistant (1st year · simple guided tasks) |
| risa | Presentation lead — dedicated to the SIH deck (1st year) |
| tejas | QA assistant & demo support (1st year · simple guided tasks) |

## How work happens here (read this first)

Every member — and every AI agent — follows the same loop:

1. **Work on your own branch** (branch name = your name): `git switch <name>`. Never commit directly to `main`.
2. **Pick your task** from `executable/<name>/checklist.md` (auto-generated from `executable/board.md`).
3. **Read the linked `docs/` file** for that task — the docs are the instructions.
4. **Do the task** in small commits; every commit message starts with the task ID.
5. **Push + open a Pull Request** into `main` titled `[TASK-ID] what you did`.
6. **Tell kv: "PR ready for review"** (or "testing done"). kv reviews — task ID, tests, docs updated in the same PR, no welfare-firewall violation.
7. **Only kv merges PRs into `main`** (kv's own PRs are reviewed by neel). Never merge your own PR.
8. After merge: `git switch main && git pull`, set your board row `[x]`.

**Task sizing:** kv and neel carry the backbone (architecture, backend, apps, complex docs). ayush, manan, risa and tejas are 1st-years with deliberately simple tasks (verify, collect, copy, record, practice). If a task feels too big, split it with kv — that is expected. New to the repo? Start with [`AGENTS.md`](AGENTS.md), then your `executable/<name>/plan-for-<name>.md`.

## Why this matters

CAPFs lost 654 personnel to suicide and ~50,000 resignations in 5 years ([ThePrint](https://theprint.in/india/654-suicides-50000-resignations-in-5-years-the-crisis-stalking-indias-capfs/1787191/)). Current MHA measures are reactive. SAARTHI makes welfare predictive — with privacy enforced in architecture, not in policy promises.
