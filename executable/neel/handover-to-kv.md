# Handover — neel → kv

> From: neel · Date: 2026-09-09 · Branch: `neel` · Status: ready for review
> Read this before the PR diff. It is long because some of it is a security
> report, and you should not find those in a diff for the first time.

## 1. TL;DR

All 17 of neel's open tasks are complete: **APP-001…010, PRIV-002, PRIV-003,
UX-001, UX-002, QA-001, QA-002, QA-003**. Board rows are `[x]`.

Three web apps now exist and run. The synthetic data generator exists. And
while writing PRIV-003 I found **12 real security defects in the shipped
backend** — including one that failed the test-plan §4 must-pass gate — and
fixed all of them, with a regression test each. §4 below is the part I most
need you to read.

```
make setup && make seed && make api        # :8000
make jawan / counsellor / commander        # :3100 / :3200 / :3300
make check                                 # boundaries, types, tests, build
make e2e                                   # 34 browser checks across all three apps
make perf                                  # TC-701 / TC-702 with a hard gate
```

## 2. What shipped

### Clients — `web/` (APP-001…010)

Three Next.js apps in the bun workspace, per ADR-0007:

| App | Port | Screens |
|---|---|---|
| `apps/jawan` | 3100 | roster home · duty · leave · 10-second check-in sheet with voice capture · instrument flow · personal trend · unit pulse · battle buddy · consent panel · who-viewed receipts · stored-data summary · settings |
| `apps/counsellor` | 3200 | ranked case queue with SLA clocks and cap state · case detail (evidence, risk-trend chart, timeline) · dual-key unmask · break-glass · session notes · outcomes · Tele-MANAS handoff |
| `apps/commander` | 3300 | unit heatmap · morale index · leading/lagging indicators · what-if simulator · attrition forecast · own check-in |

Shared packages: `tokens` · `i18n` (495 keys, en/hi parity CI-enforced) · `ui`
(30 components) · `sync` (IndexedDB outbox) · `api` (role-scoped clients behind
subpath exports) · `instruments` (the screener bank).

### Backend additions — `backend/`

Additive routers only; nothing you wrote changed shape except where §4 says so.

- `self_service.py` — `GET /app/consent` · `POST /app/consent/withdraw/{bundle_id}` ·
  **`POST /app/sync`** (batched, idempotent by `client_uuid`, per-item result) ·
  `/app/roster` · `/app/leave` · `/app/payslip` · `/app/signals/summary` ·
  `/app/me/checkins` · `/app/me/instruments` · `/app/notifications` ·
  `POST+GET /me/checkins`
- `pulse.py` — unit pulse (FR-19), k-filtered per facet
- `buddy.py` — battle buddy, coarse state only
- `counsellor.py` — case detail, timeline, session notes, risk trend
- `commander.py` — `/aggregates/units` · morale · indicators · trend · forecast ·
  simulation levers + runs
- `simulate/projection.py` — the what-if. It re-runs **your** `evaluate_rules` +
  `aggregate` over a scenario-modified HR signal vector. HR-signals only, so a
  scenario can never become a channel for individual welfare data. Nothing is
  written against a person.
- `authz.py` — caseload scoping, now enforced on `/risk`, `/signals` and every
  `/interventions` item route (see §4)

New tables: `UnitPulseRating`, `BuddyPair`, `BuddyState`, `VoiceFeature`,
`SessionNote`, `SimulationRun`, `SyncReceipt`, `AuditCheckpoint`;
`RiskScore.candidate_tier`.

### Data — `data/` (QA-001, QA-002)

`python -m data.gen --seed 42 --personnel 1000` — 1,000 personnel × 90 days,
deterministic (byte-identical checksum across runs), k ≥ 5 guard, the exact F09
persona arc, CSV export with deliberate malformed rows for your rejection path.
77 tests.

### Docs

Updated: F02, F03, F06, F07, F09, design.md, design-client-apps.md,
rbac-matrix.md, security-model.md, test-plan.md, usability-testing.md.
New: `docs/quality/threat-model.md`, `security-test-cases.md`,
`coverage-report.md`, `docs/architecture/design/mockups/` (UX-002).

## 3. Numbers

| | |
|---|---|
| Tests | **259** — backend 134, generator 77, web 48 |
| Backend coverage | **90%** · firewall 96% · kanonymity 100% · authz 98% · masking/ruleset/evaluator/expiry 100% · scorer 93% |
| Browser E2E | **34 checks**, all green (`make e2e`) |
| TC-701 recompute | **12.93 s** against a 60 s gate (Apple M4) |
| TC-702 aggregate p95 | **93 ms** against a 2 s gate |

## 4. Security defects found and fixed — please read this section

PRIV-003 was supposed to be a document. Writing it against the real code turned
up twelve things. Every one has a regression test in
`backend/tests/test_security_hardening.py`; the full case-by-case write-up is
`docs/quality/security-test-cases.md`.

| # | TC | What was wrong | Fix |
|---|---|---|---|
| 1 | TC-451 | **§4 gate failure.** `round(morale_index × n)` recovered a suppressed Amber cell of one person from the commander aggregate. | Command now gets the elevated **share** and no per-tier table at all; the share ships only when both sides of the split clear k. The table exists for counsellor/welfare, all-or-nothing. |
| 2 | TC-452 | Complement suppression filtered on a truthy count, so a unit whose other tiers were empty left one hidden cell beside a published total. | Same rewrite; `kanonymity.py` is 100% covered. |
| 3 | TC-418/419 | A counsellor could read `/risk/{any}`, `/risk/{any}/explanation` and `/signals/{any}` for **anyone** — the queue was scoped, the detail was not. | `authz.assert_subject_scope` on all of them. |
| 4 | TC-420 | A counsellor could add actions, close cases and file Tele-MANAS referrals on **another counsellor's** case. | `authz.assert_case_scope` on the three item routes. |
| 5 | TC-420b | An empty `assigned_units` read as "all units" for a welfare officer. | Empty now means none, in the queue filter and the guard. |
| 6 | — | **Handler-level denials were never audited.** `write_audit` then `raise HTTPException` unwinds through `get_db`, which rolls back — taking the audit row with it. Middleware denials were fine; every `forbid_commander` / unmask-deny / scope-deny was not. | `audit.write_deny` commits before raising. |
| 7 | TC-428 | `/jobs` and `/audit` were not in the middleware deny list — only `require_roles` stopped a commander. | Added, with `/me/checkins` explicitly allowed (self-scope, no subject selector). |
| 8 | TC-442/443 | The audit hash covered content but not `at` or sequence, so back-dating kept the chain valid and tail truncation was undetectable. | `at` + `seq` in the hash, plus an `AuditCheckpoint` row anchoring count and head hash. |
| 9 | TC-449 | `artefact_hash` was `nid("h")` — a random id. The artefact recorded that consent happened but not to what. | Real sha256 of the canonical content + `verify_artefact()`. |
| 10 | TC-454/455 | Passive and voice rows were never purged; and a client-supplied future `recorded_at` made a row immortal. | Expiry covers both; capture dates are clamped to a 30-day offline window. |
| 11 | TC-438 | Break-glass was unlimited and uncountersigned — cheaper than the dual-key path it is supposed to be more expensive than. | Weekly cap per counsellor; above it, an explicit oversight acknowledgement and a substantive reason, and every welfare officer is notified. Never hard-blocked — imminent harm must stay reachable. |
| 12 | TC-424 | The quarantine report was addressable by a guessable `batch_id` from any ingest account, and returned raw HR payloads to admin and auditor. | Scoped to the submitting principal; payload withheld from roles with no content grant; every read audited. |
| 13 | TC-415/456/457/458 | Committed dev secret usable in production · CORS `*` with credentials · no login throttle · unbounded CSV upload. | `Settings.assert_deployable()` refuses a production start on the dev secret or SQLite; CORS allow-list; per-username login throttle; 8 MB upload bound. |

### One rules-engine bug, separately

`_downgrade_confirmations` counted the **published** tier, which is the tier
hysteresis had just held. So the counter could never reach its threshold and a
recovering person stayed flagged forever — the F09 arc could not close, and
demo-runbook beat 7 ("score trend drops") did not reproduce.

Fix: `RiskScore.candidate_tier` stores the pre-hysteresis tier and the counter
reads that. Tests in `backend/tests/test_hysteresis_release.py`. The persona now
runs 67 → 45 → 30 and lands **green** on day 90.

### Three accessibility defects

Measured against design.md's own floors, in `tokens.json`:
care-chip labels 2.03:1 (amber) to 4.29:1 (red) against a 4.5:1 floor; the
saffron CTA white-on-saffron at 2.76:1; the focus ring at 2.55:1 against a 3:1
rule. Fixed with `--sa-color-state-ink-*`, `--sa-color-accent-saffron-ink` and
`--sa-color-focus` — same hues, no visual identity change. **The lint now
measures all 18 pairs on every build**, so this cannot drift back.

## 5. What I need from you

1. **Review §4.** Those are changes to your files. I kept every edit additive
   where I could, but `kanonymity.py`, `audit.py`, `security.py`, `config.py`,
   `firewall.py`, `expiry.py`, `consent.py`, `scorer.py` and three routers have
   real behaviour changes, and `test_privacy.py::test_k_anonymity_3bn_ok` now
   asserts a stronger contract than it did.
2. **ADR-0007** — the web-first decision is implemented but still a draft at
   `executable/neel/adr-0007-draft.md`. It needs to land as
   `docs/architecture/decisions/0007-web-first-clients.md`, which is your file.
3. **Two branches are unmerged into `main`** and I did not touch them, because
   only you merge: `origin/manan` (3 commits, PRIV-005/006) and `origin/tejas`
   (1 commit). Note tejas hand-edited his `checklist.md`, which is generated —
   his statuses need to move into `board.md` or the next
   `sync-checklists.py` run will overwrite them.
4. **TC-505** is referenced in test-plan.md §2 but defined nowhere. Define it or
   drop the reference.
5. **The demo needs `make generate`, not just `make seed`.** With the 12-person
   persona seed, 3BN is correctly suppressed on the commander heatmap and the
   "3rd Bn, 22% elevated fatigue" line never appears. The 1,000-personnel
   fixture gives battalions of ~200 where the numbers publish. Worth updating
   the runbook's T-30 checklist.

## 6. Known gaps — not fixed, deliberately

- **No device lab.** TC-606/607 (API-26-class Android, screen reader) are
  unrun. The protocol is written (`usability-testing.md`).
- **ISI ships without item text.** It is copyrighted; a paraphrase would break
  the validated-instruments-only rule. Scoring, bands and the flow are
  implemented behind `licence: "licence_pending"`.
- **Hindi is not clinically adapted.** Every instrument is
  `adaptation: "review_pending"`; English stays authoritative for scoring and
  the app says so on screen.
- **Encryption at rest, TLS, key management, a scheduler for the expiry job** —
  deployment concerns, still documented-only. Listed in security-model.md's
  verification status.
- **TC-432** (two accounts, one human, defeats dual-key) is accepted and
  compensated by audit + subject notification, not fixed.
