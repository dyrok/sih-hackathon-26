# SAARTHI — one entry point for setup, seed, run, test.
#
# The jury checklist asks for "setup in 5 minutes" on a laptop with no network
# guarantees, so every target below works offline once dependencies are in place
# and none of them reaches a cloud service (ADR-0006, NFR-03).

SHELL := /bin/bash
PY    := backend/.venv/bin/python
PIP   := backend/.venv/bin/pip

.DEFAULT_GOAL := help

.PHONY: help
help: ## show this list
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

.PHONY: setup
setup: setup-backend setup-web ## install everything (backend venv + bun workspace)

.PHONY: setup-backend
setup-backend: ## create backend/.venv and install requirements
	@test -d backend/.venv || python3 -m venv backend/.venv
	@$(PIP) install -q -r backend/requirements.txt
	@echo "backend ready: $$($(PY) --version)"

.PHONY: setup-web
setup-web: ## install the bun workspace
	@cd web && bun install

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

.PHONY: seed
seed: ## seed the demo persona + unit background (fast path before a demo)
	@cd backend && .venv/bin/python -m app.seed

.PHONY: generate
generate: ## generate the full synthetic population (1000 personnel x 90 days)
	@$(PY) -m data.gen --seed 42 --personnel 1000

.PHONY: generate-preview
generate-preview: ## show the persona arc + row counts without writing anything
	@$(PY) -m data.gen --seed 42 --personnel 1000 --dry-run

.PHONY: generate-csv
generate-csv: ## export the population as CSVs for the HR ingestion path
	@$(PY) -m data.gen --seed 42 --personnel 1000 --format csv --out-dir ./.data-csv
	@echo "wrote ./.data-csv"

.PHONY: reset
reset: ## delete the demo database and re-seed from scratch
	@rm -f backend/saarthi.db
	@$(MAKE) --no-print-directory seed

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

.PHONY: api
api: ## run the Core API on :8000
	@cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

.PHONY: jawan
jawan: ## run the jawan PWA on :3100
	@cd web && bun run dev:jawan

.PHONY: counsellor
counsellor: ## run the counsellor console on :3200
	@cd web && bun run dev:counsellor

.PHONY: commander
commander: ## run the commander dashboard on :3300
	@cd web && bun run dev:commander

.PHONY: demo
demo: ## print the demo checklist (what to open, in what order)
	@echo "SAARTHI demo — start each in its own terminal:"
	@echo "  1. make api          http://127.0.0.1:8000/docs"
	@echo "  2. make jawan        http://localhost:3100   jawan.demo / saarthi"
	@echo "  3. make counsellor   http://localhost:3200   counsellor.a / saarthi"
	@echo "  4. make commander    http://localhost:3300   commander.3bn / saarthi"
	@echo ""
	@echo "The firewall beat: as commander.3bn, open the browser console and run"
	@echo "  fetch('http://127.0.0.1:8000/welfare/personnel/CR-DEMO-01')"
	@echo "It answers 403 and writes an audit row the jawan can see in 'who viewed my data'."
	@echo ""
	@echo "Runbook: docs/quality/demo-runbook.md"

# ---------------------------------------------------------------------------
# Quality gates
# ---------------------------------------------------------------------------

.PHONY: test
test: test-backend test-data test-web ## run every test suite

.PHONY: test-backend
test-backend: ## pytest (API, firewall, RBAC, security regressions)
	@cd backend && .venv/bin/python -m pytest -q

.PHONY: test-data
test-data: ## pytest for the synthetic data generator (determinism, persona arc, k>=5)
	@$(PY) -m pytest data/tests -q

.PHONY: test-web
test-web: ## bun test (offline queue, instruments, api wire format)
	@cd web && bun test

.PHONY: coverage
coverage: ## backend coverage report (gate: overall >= 80%, firewall + engine >= 90%)
	@cd backend && .venv/bin/python -m pytest -q --cov=app --cov-report=term-missing:skip-covered

.PHONY: lint
lint: ## architectural boundaries: role isolation, tokens-only, i18n keys, en/hi parity
	@cd web && bun scripts/lint-boundaries.mjs

.PHONY: typecheck
typecheck: ## tsc --noEmit across the three apps
	@cd web && bun run typecheck

.PHONY: build
build: ## production build of all three web apps
	@cd web && bun run build

.PHONY: e2e
e2e: ## browser end-to-end across all three apps (needs the API + the three dev servers running)
	@cd web && bun e2e/smoke.mjs

.PHONY: perf
perf: ## TC-701/TC-702 performance envelope on the 1000-personnel fixture
	@$(PY) scripts/perf.py --gate

.PHONY: harness
harness: ## ML-002 validation harness — persona arc replay + threshold sweep
	@cd backend && .venv/bin/python -m app.ml.harness

.PHONY: check
check: lint typecheck test build ## everything CI would run
	@echo "all gates green"
