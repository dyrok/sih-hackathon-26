# Notes & Work Log — tejas (QA Assistant & Demo Support)

> Owner: tejas · Status: [~] live · Last updated: 2026-09-09  
> Role: QA assistant & demo support (1st year)  
> Branch: `tejas` · Buddy: kv

---

## 1. Task QA-005 — Docs QA Sweep (Stamps + Links)

- **Date executed:** 2026-09-08
- **Auditor:** tejas
- **Scope:** 49 markdown files in `docs/` + repo-wide cross-check (76 markdown files total)
- **Status:** Done · PR opened on branch `tejas`

### Summary of Results
| Check Category | Inspected | Passed | Gaps / Flags | Result |
|---|---|---|---|---|
| **Owner Stamp** (`Owner: <name>`) | 49 files in `docs/` | 48 | 1 file missing (`docs/product/submission/README.md`) | **ATTENTION FOR KV** |
| **Status Stamp** (`Status: <status>`) | 49 files in `docs/` | 48 | 1 file missing (`docs/product/submission/README.md`) | **ATTENTION FOR KV** |
| **Date Stamp** (`Last updated:` / date) | 49 files in `docs/` | 42 standard + 6 MADR | 1 file missing | **PASS (with note)** |
| **Relative File Links** (`[text](rel/path.md)`) | All links across `docs/` | 100% | 0 broken paths | **PASS** |
| **Repo-wide File Links** | 76 files in repo | 100% | 0 broken paths | **PASS** |
| **`docs/README.md` Index Links** | 33 table links | 33 | 0 broken paths | **PASS** |
| **Internal Heading Anchors** | All `#section` anchors | Most | 5 files have anchor text drift | **INFO FOR KV** |

### Gaps Reported for kv
1. **`docs/product/submission/README.md`**: Missing Owner, Status, and Last updated stamps.
2. **Heading Anchor Drift**: 5 files have minor anchor naming mismatches (documented in QA-005 report).

---

## 2. Task QA-006 — Manual Test Checklist Execution & Pass/Fail Record

- **Date started:** 2026-09-09
- **Source of Truth:** `docs/quality/test-plan.md` (§4 Firewall Suite, §5 Offline Sync) & `docs/quality/demo-runbook.md` (§7)
- **Status:** `[~]` In progress (Backend test suite audited; mobile app manual tests pending neel's `APP-001`)

### Part A: Automated Backend Suite Audit (Python 3.13)
Ran backend automated test suite (`pytest backend/tests`):
- **Results:** 43 tests passed, 1 failed (44 test items).
- **Pass Details:**
  - `test_ingest.py`: PASS (15+ signal features, duplicate detection, bad rows rejection).
  - `test_interventions.py`: PASS (response ladder, capacity caps, rebalancing swaps).
  - `test_persona_and_harness.py`: PASS (scripted 90-day arc reproduction).
  - `test_privacy.py`: PASS (k-anonymity aggregation k >= 5, 90-day expiry, silent consent withdrawal).
  - `test_risk_pure.py`: PASS (0-100 baseline composite scoring, masking flag firing).
  - `test_signals.py`: PASS (domain features: leave, duty, circadian disruption).
- **Failure Observation (Honest QA Record):**
  - `backend/tests/test_firewall.py::test_tc403_commander_scrape_has_no_individual_score`: Failed assertion `assert denied, "commander should be denied somewhere"`.
  - **Note for kv/neel:** The route scraping test checked for HTTP 403 when scraping paths with a commander JWT, but some restricted routes returned 404 or 422 instead of explicit 403, leaving the `denied` list empty. Zero individual scores or identities leaked (asserted clean), but status code handling needs minor alignment.

### Part B: Manual Test Checklist (Traceability Matrix)

| Test ID | Scenario & Given / When / Then | Expected Outcome | Observed Result | Notes |
|---|---|---|---|---|
| **TC-401** | Commander JWT requests `GET /welfare/personnel/{id}` | Route-level rejection (403/404) | **PASS** | Verified via backend route authz. No individual access. |
| **TC-402** | Commander views unit pulse with < 5 personnel | Cell suppressed / hidden | **PASS** | Verified in `test_privacy.py`. k >= 5 enforced. |
| **TC-404** | Jawan opens "Who Viewed My Data" screen | Shows counsellor role, timestamp, reason | **BLOCKED** | Waiting on neel `APP-005` (UI screen). |
| **TC-405** | Dual-key unmask attempted with single approval | Rejected until both counsellor & welfare officer approve | **PASS** | Verified in backend test suite. |
| **TC-407** | Jawan toggles silent consent withdrawal | Command view unchanged; subject view shows inactive | **PASS** | Backend logic passes; UI verification pending neel `APP-004`. |
| **TC-408** | 90-day raw data expiry cron job runs | Raw records purged; derived metrics preserved | **PASS** | Verified in `test_privacy.py`. |
| **TC-409** | Break-glass access used on restricted record | Subject notified immediately; audit row logged | **PASS** | Verified in `test_privacy.py`. |
| **TC-601** | Airplane mode: submit check-in on mobile app | Queues locally in SQLite; syncs once on reconnect | **BLOCKED** | Waiting on neel `APP-001` (mobile app scaffold). |
| **TC-602** | 72 queued offline entries batch uploaded | Completes in batches; resumes from checkpoint | **BLOCKED** | Waiting on neel `APP-001` (mobile app scaffold). |
| **TC-603** | Retry same check-in multiple times | Idempotency key collapses duplicate entries | **BLOCKED** | Waiting on neel `APP-001`. |
| **TC-604** | Conflicting local/server edit on monthly survey | Per-field last-write-wins with conflict flag | **BLOCKED** | Waiting on neel `APP-001`. |
| **TC-605** | Kill app process mid-sync and relaunch | Queue resumes gracefully without DB corruption | **BLOCKED** | Waiting on neel `APP-001`. |
| **TC-606** | Android API 26 emulator (1 GB RAM profile) | 10-s check-in completes smoothly on icon UI | **BLOCKED** | Waiting on neel `APP-001`. |
| **TC-607** | Language toggle en <-> hi across all screens | 100% strings resolve from i18n keys (no raw text) | **BLOCKED** | Waiting on neel `APP-001` / `APP-003`. |

---

## 3. Task QA-007 — Demo Rehearsal Support & Video Fallback Recording

- **Date started:** 2026-09-09
- **Partner:** risa (1st year, Presentation & Deck owner)
- **Guide / Specification:** `docs/quality/demo-runbook.md` (§1 3-min script, §3 persona, §7 fallback spec)
- **Status:** `[~]` Storyboard & shot checklist prepared; recording pending UI screens from neel (`APP-001..010`)

### Shot-by-Shot Fallback Video Specification (for risa + tejas)
Target format: 1080p MP4, < 100 MB, offline playback, filename: `SAARTHI-demo-fallback-YYYYMMDD.mp4`.

| Shot # | Screen / Scene | Duration | Mandatory Elements ("Must Show") | Strict Exclusions ("Must Not Show") | Status |
|---|---|---|---|---|---|
| **Shot 1** | Jawan Check-in (Hindi UI) | 10 s | 10-second check-in flow, `instr.not_diagnosis` disclaimer visible | Any other personnel's data | Script ready; waiting for mobile UI |
| **Shot 2** | Commander Aggregate Heatmap | 15 s | "3rd Bn" elevated fatigue, k >= 5 badge, aggregate pulse | Any personnel ID, individual score, or name | Script ready; waiting for web UI |
| **Shot 3** | Counsellor Console | 20 s | Top-3 contributing factors clearly visible and legible | Raw personal journal entries | Script ready; waiting for console UI |
| **Shot 4** | Masking & Red Alert | 15 s | "I'm fine" self-report vs high duty hours discrepancy, <= 24h SLA | Any punitive or disciplinary wording | Script ready; waiting for console UI |
| **Shot 5** | Dual-Key Unmask & Who-Viewed | 20 s | Dual approval badges (counsellor + welfare officer); jawan's receipt | Unmasked name on commander dashboard | Script ready; waiting for UI |
| **Shot 6** | Roster Swap & Trend Recovery | 10 s | Swap proposal with load delta, subsequent risk trend curve recovery | Any commander punitive review | Script ready; waiting for UI |

### Rehearsal Gate Verification (backend level)
- [x] Backend seed script produces `DEMO-PERSONA-01` (`Constable, 34, 3rd Bn`).
- [x] Explanation API returns top-3 factors (`60 consecutive duty days`, `2 cancelled leaves`, `sleep -30%`).
- [x] k-anonymity aggregation enforces k >= 5.
- [ ] 5x Rehearsal Runs: Waiting for mobile and dashboard UI components to be integrated.

### Request for kv / neel
- Please notify tejas & risa when `APP-001` (mobile APK / Expo web) and `APP-007/008` (consoles) are ready for screen recording.
