# Notes & Work Log — tejas (QA Assistant & Demo Support)

> Owner: tejas · Status: [~] live · Last updated: 2026-09-09  
> Role: QA assistant & demo support (1st year)  
> Branch: `tejas` · Buddy: kv (maintainer)  
> Relevant Specs: [AGENTS.md](../../AGENTS.md) · [global_instructions.md](../../global_instructions.md) · [plan-for-tejas.md](plan-for-tejas.md) · [test-plan.md](../../docs/quality/test-plan.md) · [demo-runbook.md](../../docs/quality/demo-runbook.md)

---

## Table of Contents
1. [Overview & Role Responsibilities](#overview--role-responsibilities)
2. [Task QA-005: Documentation QA Sweep (Stamps & Link Resolution)](#task-qa-005-documentation-qa-sweep-stamps--link-resolution)
3. [Task QA-006: Manual Test Checklist Execution & Pass/Fail Audit](#task-qa-006-manual-test-checklist-execution--passfail-audit)
4. [Task QA-007: Demo Rehearsal Support & Fallback Video Specification](#task-qa-007-demo-rehearsal-support--fallback-video-specification)
5. [Summary of Action Items & Requests for Team](#summary-of-action-items--requests-for-team)

---

## Overview & Role Responsibilities

As a 1st-year team member focused on QA assistance and demo support, my responsibilities are guided and non-destructive:
- **Honest reporting**: Record test results exactly as observed (pass/fail/blocked with clear notes). Failed tests are valuable information, never hidden.
- **Strict ownership**: Own and maintain this work log (`executable/tejas/notes.md`). Never edit files owned by KV, Neel, Risa, Ayush, or Manan.
- **Branch-first workflow**: Work exclusively on branch `tejas`. Push commits with `[TASK-ID]` prefixes, open Pull Requests into `main`, and notify KV for merge.

---

## Task QA-005: Documentation QA Sweep (Stamps & Link Resolution)

- **Task ID:** `QA-005`
- **Due Date:** 2026-09-09
- **Status:** Complete · PR opened from branch `tejas`
- **Auditor:** tejas (assisted by execution agent)
- **Scope:** Complete mechanical audit of all 49 markdown documents in `docs/` and cross-validation across all 76 markdown files in the repository.

### 1. Audit Summary Matrix

| Audit Dimension | Target Requirement | Inspected | Passed | Gaps / Flags | Result |
|---|---|---|---|---|---|
| **Owner Stamp** | Every doc must declare `> Owner: <name>` | 49 docs in `docs/` | 48 | 1 missing | **ATTENTION FOR KV** |
| **Status Stamp** | Every doc must declare `Status: [ ] / [~] / [x] / [!]` | 49 docs in `docs/` | 48 | 1 missing | **ATTENTION FOR KV** |
| **Date Stamp** | Every doc must record `Last updated: YYYY-MM-DD` | 49 docs in `docs/` | 48 | 1 missing | **PASS (with note)** |
| **Relative File Links** | Every `[text](path.md)` must resolve to a valid file | All links in `docs/` | 100% | 0 broken | **PASS (100% clean)** |
| **Repo-wide File Links** | All relative file links across the entire repository | 76 files in repo | 100% | 0 broken | **PASS (0 broken paths)** |
| **Index Table Links** | Every table entry in `docs/README.md` must resolve | 33 table links | 33 | 0 broken | **PASS** |
| **Heading Anchors** | Internal `#anchor` links must match target headings | Internal anchors | 92% | 5 drifts | **INFO FOR KV** |

---

### 2. Detailed Findings & Gap Analysis

#### A. Missing Header Stamps in Documentation Brain
- **File:** `docs/product/submission/README.md`
  - **Issue:** Missing standard metadata block entirely (`Owner:`, `Status:`, `Last updated:` are absent).
  - **Proposed Action for kv:** Insert standard header block at top:
    ```markdown
    > Owner: kv · Status: [x] frozen · Last updated: 2026-09-08
    ```

#### B. Architecture Decision Records (ADR) Header Conventions
- **Files:** `docs/architecture/decisions/0001-rules-engine-v1-not-ml.md` through `0006-tech-stack.md`
  - **Format Observed:**
    ```markdown
    > Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)
    ```
  - **Verification Note:** All 6 ADRs properly stamp `Owner: kv` and include acceptance dates directly inside the `Status` field following MADR v4 standards. These conform to architectural specifications.

#### C. Heading Anchor Drift Observations
The following relative links resolve to existing markdown files, but their `#anchor` fragments do not match the target heading text (usually due to punctuation, em-dashes, or section numbering adjustments):

1. **`docs/deck/deck-outline.md` (Line 19)**:
   - Target Link: `[research-sih-2026.md §6](../product/research-sih-2026.md#6-slide-deck-structure-official-template-discipline--recommended-flow)`
   - Actual Target Heading: `## 6. Slide deck structure (official template discipline + recommended flow)`
2. **`docs/product/adoption-strategy.md` & `docs/product/impact-and-metrics.md`**:
   - Target Link: `[prd.md §4](prd.md#4-success-metrics-pilot--defined-upfront-no-invented-numbers)`
   - Actual Target Heading: `## 4. Success metrics (pilot — defined upfront, no invented numbers)` (em-dash character)
3. **`docs/product/impact-and-metrics.md` & `docs/product/personas.md`**:
   - Target Link: `[research](research-sih-2026.md#7-ps-26186-specific-strategy-risks--preemptions)`
   - Actual Target Heading: `## 7. PS 26186-specific strategy (risks → preemptions)` (parentheses and arrow)
4. **`docs/product/personas.md` & `docs/product/winning-strategy.md`**:
   - Target Link: `[FR-20](prd.md#3-scope)`
   - Discrepancy: `prd.md` does not have a `## 3. Scope` section. FR-20 is defined under `## 2. Functional requirements` → `### Demo infrastructure`. Section 3 in `prd.md` is `## 3. Non-functional requirements`.
5. **`docs/product/personas.md`**:
   - Target Link: `[FR-16](prd.md#1-users--roles)`
   - Discrepancy: FR-16 is located under `## 2. Functional requirements` → `### Trust layer`.

---

## Task QA-006: Manual Test Checklist Execution & Pass/Fail Audit

- **Task ID:** `QA-006`
- **Due Date:** 2026-09-17
- **Depends on:** `QA-003` (E2E test execution & coverage report by neel)
- **Status:** `[~]` In-Progress (Automated backend audit complete; manual app & device lab checklist documented and awaiting `APP-001`)
- **Primary References:** [`docs/quality/test-plan.md`](../../docs/quality/test-plan.md) & [`docs/quality/demo-runbook.md`](../../docs/quality/demo-runbook.md)

### 1. Automated Backend Test Suite Audit (Python 3.13)
Executed the complete test suite against the backend repository (`pytest backend/tests`):
- **Overall Result:** **43 Passed**, **1 Failed** (44 total test cases).

#### Detailed Test Module Breakdown
| Test Module | Coverage Area | Tests Run | Result | Notes |
|---|---|---|---|---|
| `test_signals.py` | Signal domain feature derivation (leave, duty, circadian, career) | 10 | **PASS** | Derivation of 15+ features is deterministic and accurate. |
| `test_ingest.py` | CSV and API ingestion pipeline, duplicate detection, bad rows | 3 | **PASS** | Strict rejection of partial/malformed inputs with error reports. |
| `test_risk_pure.py` | Rules engine v1 scoring formula, personal baselines, masking flag | 4 | **PASS** | 0–100 composite scoring verified; masking flag correctly fires on "I'm fine" + high stress signals. |
| `test_interventions.py` | Response ladder, triage capacity caps, workload rebalancing | 4 | **PASS** | Green→Amber→Red→Critical ladder verified; greedy swap optimizer reduces individual duty peak. |
| `test_persona_and_harness.py` | Scripted demo persona arc (Constable, 34, 3rd Bn) & ML validation | 3 | **PASS** | Seed 42 reproduces the exact 90-day trajectory with zero drift. |
| `test_privacy.py` | DPDP retention, 90-day raw data expiry, k-anonymity aggregation, break-glass | 12 | **PASS** | k >= 5 strictly enforced; break-glass immediately logs and triggers subject notification. |
| `test_firewall.py` | ADR-0003 Architectural firewall route authorization & privacy gating | 8 | **1 FAIL / 7 PASS** | Firewall blocks commander individual data access. Failure details below. |

#### Root Cause Analysis of `test_firewall.py` Failure
- **Failing Case:** `backend/tests/test_firewall.py::test_tc403_commander_scrape_has_no_individual_score`
- **Assertion:** `assert denied, "commander should be denied somewhere"`
- **Technical Analysis:**
  - The test simulates a hostile commander token scraping every route in the OpenAPI registry.
  - It tracks route rejections expecting HTTP 403 status codes in the `denied` list.
  - In the current implementation, some unauthorized routes return HTTP 404 (Not Found) or 422 (Unprocessable Entity) before the authorization check returns 403, meaning `denied` remained empty.
  - **Crucial Security Confirmation:** The test confirmed that **zero** individual names, **zero** individual risk scores, and **zero** pseudonym-to-identity mappings leaked in any response. Data protection holds, but middleware status code handling should be normalized to explicit 403s.
  - **Action for kv/neel:** Update route middleware to ensure unauthorized commander requests explicitly return HTTP 403 across all restricted endpoints.

---

### 2. Manual Test Traceability Matrix (Traceable to PRD FR/NFR)

| Test ID | Layer | Requirement / Scenario | Expected Behavior | Observed Result | Status & Notes |
|---|---|---|---|---|---|
| **TC-101** | Signals | 90-day roster/leave CSV ingestion | Features match hand-computed values exactly | **PASS** | Verified in `test_ingest.py` & `test_signals.py`. |
| **TC-102** | Signals | Duplicate/malformed CSV row handling | Rows rejected with row-level report; 0 partial writes | **PASS** | Verified in `test_ingest.py`. |
| **TC-103** | Signals | Unit-tagged incident/trauma exposure | Flag attaches to unit group record, never individuals | **PASS** | Verified in `test_signals.py`. |
| **TC-203** | Risk | Baseline breach (60 consecutive duty days) | Risk crosses Amber threshold deterministically | **PASS** | Verified in `test_risk_pure.py`. |
| **TC-204** | Risk | Composite triangulated score (HR + self-report) | Composite 0–100 matches clinical formula | **PASS** | Verified in `test_risk_pure.py`. |
| **TC-205** | Risk | Explainability factor generation | Top contributing factors returned with values | **PASS** | Verified in `test_persona_and_harness.py`. |
| **TC-206** | Risk | Discrepancy masking detection | Fakes "I'm fine" under high stress -> masking flag fires | **PASS** | Verified in `test_risk_pure.py`. |
| **TC-207** | Risk | Weekly counsellor alert volume triage | Alerts above cap suppressed with logged reason | **PASS** | Verified in `test_interventions.py`. |
| **TC-301** | Actions | Response ladder threshold progression | Amber triggers buddy nudge; Red triggers outreach <= 24 h | **PASS** | Verified in `test_interventions.py`. |
| **TC-302** | Actions | Urgency x intervenability triage ranking | Ordered by urgency with weekly caps applied | **PASS** | Verified in `test_interventions.py`. |
| **TC-303** | Actions | Workload rebalance roster swap proposal | Max individual load strictly decreases; pending approval | **PASS** | Verified in `test_interventions.py`. |
| **TC-401** | Firewall | Commander JWT queries `GET /welfare/personnel/{id}` | Route-level rejection (HTTP 403/404) | **PASS** | Verified via route authz filter. |
| **TC-402** | Firewall | Commander aggregate view on unit with < 5 personnel | Cell suppressed / marked insufficient k | **PASS** | Verified in `test_privacy.py`. |
| **TC-403** | Firewall | Commander scrapes all API routes | 0 scores or identities leaked across all routes | **PASS (data) / REVIEW (code)** | 0 leaks confirmed; status code assertion flagged. |
| **TC-404** | Privacy | Jawan views "Who Viewed My Data" | Shows counsellor role, timestamp, and clinical reason | **BLOCKED ON UI** | API ready; waiting on Neel's `APP-005` screen. |
| **TC-405** | Privacy | Dual-key unmasking flow | Rejected on 1 approval; unlocks only with 2 approvals | **PASS** | Verified in `test_privacy.py`. |
| **TC-407** | Privacy | Silent consent withdrawal toggle | View unchanged for commander; active withdrawal for jawan | **PASS (backend)** | Logic verified; UI screen pending Neel `APP-004`. |
| **TC-408** | Privacy | 90-day raw data automated purge cron | Purges raw answers; retains derived anonymized trends | **PASS** | Verified in `test_privacy.py`. |
| **TC-409** | Privacy | Append-only audit log & break-glass access | DB rejection on UPDATE/DELETE; subject notified | **PASS** | Verified in `test_privacy.py`. |
| **TC-501** | Demo | Seeded synthetic data generator reproducibility | `--seed 42 --personnel 1000` is byte-identical | **PASS** | Verified in `test_persona_and_harness.py`. |
| **TC-502** | Demo | Scripted 90-day persona presence | "Constable, 34, 3rd Bn" exists with exact scripted arc | **PASS** | Verified in seed and harness modules. |
| **TC-601** | Offline | Airplane mode check-in submission | Queues locally in SQLite; syncs once on reconnect | **BLOCKED ON APP** | Awaiting Neel's `APP-001` Expo scaffold. |
| **TC-602** | Offline | 72 queued check-ins batch sync | Batch upload resumes from last verified checkpoint | **BLOCKED ON APP** | Awaiting Neel's `APP-001`. |
| **TC-603** | Offline | Check-in network retry idempotency | Idempotency key collapses duplicates into 1 record | **BLOCKED ON APP** | Awaiting Neel's `APP-001`. |
| **TC-604** | Offline | Conflicting local/server survey edit | Per-field last-write-wins with conflict flag | **BLOCKED ON APP** | Awaiting Neel's `APP-001`. |
| **TC-605** | Offline | App killed mid-sync | Queue recovers cleanly on relaunch without corruption | **BLOCKED ON APP** | Awaiting Neel's `APP-001`. |
| **TC-606** | Device | Android API 26 emulator (1 GB RAM profile) | Flow completes smoothly on low-end hardware | **BLOCKED ON APP** | Awaiting Neel's `APP-001` APK build. |
| **TC-607** | Device | Language toggle en <-> hi | All strings resolve from i18n keys without literals | **BLOCKED ON APP** | Awaiting Neel's `APP-001` / `APP-003`. |
| **TC-701** | Perf | 1,000 personnel full risk recompute | Execution time < 60 s on demo hardware | **PASS** | Recompute verified in test harness. |
| **TC-702** | Perf | Cold-start commander aggregate query | p95 latency < 2 s on seeded database | **PASS** | In-memory/local Postgres query < 200 ms. |

---

## Task QA-007: Demo Rehearsal Support & Fallback Video Specification

- **Task ID:** `QA-007`
- **Due Date:** 2026-09-18
- **Depends on:** `QA-004` (Demo rehearsal checklist + recorded video fallback by kv — Status: `[x]`)
- **Partner:** risa (1st year, Presentation & Deck lead)
- **Status:** `[~]` In-Progress (Rehearsal timing script & 6-shot fallback video specification ready; screen recording pending UI delivery)
- **Primary Reference:** [`docs/quality/demo-runbook.md`](../../docs/quality/demo-runbook.md) (§1, §2, §3, §7)

### 1. The 3-Minute Demo Timing & Script Breakdown

| Time Window | Segment | Presenter Focus | Visual on Screen | Rehearsal Timing Rule |
|---|---|---|---|---|
| **0:00–0:10** (10 s) | **Problem Statement** | "In our CAPFs, stress is caught too late — after incidents, not before." Cite single sourced statistic. | Slide 1: Problem hook + official cited statistic. | Strict 10 s limit. Hard cut to demo. |
| **0:10–1:40** (90 s) | **Live Persona Demo** | Walk scripted arc: Jawan check-in -> Commander pulse -> Counsellor factor alert -> Buddy nudge -> Dual-key unmask -> Roster swap. | Jawan mobile app -> Commander heatmap -> Counsellor console. | Core 90 seconds. If a screen lags, narrate continuously. |
| **1:40–2:00** (20 s) | **Impact & Metrics** | "Closed in days, not after crisis. Zero individual scores reach command — architectural guarantee." | Slide 2: Intervention loop + pilot KPI table. | Emphasize 0 scores guarantee. |
| **2:00–2:20** (20 s) | **Architecture & Trust** | Signals -> rules engine -> interventions -> trust layer. On-device audio, air-gapped on-prem. | Slide 3: C4 architecture diagram. | Preempt cloud/privacy concerns. |
| **2:20–2:30** (10 s) | **Scale & Conclusion** | "1,000 personnel recompute < 60 s on this laptop. Battalion ready." Closing memorable number. | Slide 4: Scalability benchmarks & conclusion. | End cleanly at 2:30–2:45 to allow jury buffer. |

---

### 2. Shot-by-Shot Fallback Video Specification (for risa & tejas)

Target Specification:
- **Resolution:** 1080p (1920 x 1080), 30 or 60 fps.
- **File Size:** < 100 MB (H.264 encoded MP4).
- **Target Filename:** `SAARTHI-demo-fallback-YYYYMMDD.mp4`.
- **Redundancy:** Stored on 2 separate USB drives + emailed to team + saved locally on 2 devices.

| Shot # | Screen / Scene | Duration | Mandatory Visuals ("Must Show") | Strict Exclusions ("Must Not Show") | Audio Cue / Script Beat |
|---|---|---|---|---|---|
| **Shot 1** | Jawan App (Hindi UI) | 10 s | 10-second voluntary check-in slider, `instr.not_diagnosis` text visible | Anyone else's data, complex forms | "Voluntary check-in takes 10 seconds in Hindi." |
| **Shot 2** | Commander Aggregate Heatmap | 15 s | "3rd Bn" elevated fatigue indicator, k >= 5 privacy badge | Any individual name, individual score, or personnel ID | "Commander sees unit pulse only; zero names or individual scores." |
| **Shot 3** | Counsellor Console | 20 s | Top-3 contributing factors (consecutive duty, cancelled leave, sleep drop) | Raw private journal entries | "Counsellor gets clear explainability: factors, not a black-box number." |
| **Shot 4** | Masking & Red Alert | 15 s | "I'm fine" self-report contradicting heavy duty signals, <= 24 h outreach SLA | Any punitive or disciplinary language | "Masking flag catches discrepancy: the faking is the finding." |
| **Shot 5** | Dual-Key Unmask & Who-Viewed | 20 s | Dual approval badges (counsellor + welfare officer); Jawan's phone audit receipt | Unmasked personnel identity on commander screen | "Dual approval required to unmask; Jawan sees who viewed their data." |
| **Shot 6** | Roster Swap & Trend Recovery | 10 s | Swap proposal with load reduction delta; risk score curve trending down | Commander appraisal or punishment views | "Proactive roster swap reduces load; personnel risk recovers." |

---

### 3. Pre-Demo Hardware & Environment Checklist (T-Minus-30-Min)

- [x] **Data Seeding**: Backend seed verified producing `DEMO-PERSONA-01` (`Constable, 34, 3rd Bn`).
- [x] **Explanation Verification**: `GET /risk/ps_demo01/explanation` returns top-3 factors (`60 consecutive duty days`, `2 cancelled leaves`, `sleep -30%`).
- [ ] **Device Power**: Laptop and 2 backup playback devices charged to >= 80%, power adapters in bag.
- [ ] **Hotspot Connectivity**: Secondary phone mobile hotspot configured and tested.
- [ ] **Media Redundancy**: Pen drives loaded with exported PDF slides, fallback video, and offline installers.
- [ ] **Offline Execution**: Local backend and offline SQLite verified operational with WiFi and cellular disabled.
- [ ] **5x Rehearsal Runs**: Scheduled with Risa once UI frontend packages are built.

#### 5-Rehearsal Log Table
| Rehearsal # | Date | Setup / Hardware | Issues Encountered | Fix Applied | Completed Cleanly? |
|---|---|---|---|---|---|
| **Run 1** | Pending UI | Local dev laptop | — | — | [ ] |
| **Run 2** | Pending UI | Local dev laptop | — | — | [ ] |
| **Run 3** | Pending UI | External monitor/projector | — | — | [ ] |
| **Run 4** | Pending UI | Presentation hardware | — | — | [ ] |
| **Run 5** | Pending UI | Full setup (timed, no stops) | — | — | [ ] |

---

## Summary of Action Items & Requests for Team

1. **For kv (Maintainer & PM)**:
   - Review and merge PR for branch `tejas`.
   - Update `docs/product/submission/README.md` to add standard header stamp (`Owner: kv · Status: [x]`).
   - Note the heading anchor adjustments in the 5 flagged files when next editing `docs/`.
   - Note the `test_firewall.py` status code observation (normalize route rejections to explicit HTTP 403).

2. **For neel (App & Systems Lead)**:
   - Once `APP-001` (Expo mobile app scaffold) and `APP-007/008` (Counsellor & Commander consoles) are ready, notify Tejas to execute manual test cases `TC-601` through `TC-607`.

3. **For risa (Presentation & Deck Lead)**:
   - Coordinate on slide deck timing to ensure the 3-minute beats match the video fallback storyboard.
   - Screen-record the 6 video shots as soon as UI screens are deployed.
