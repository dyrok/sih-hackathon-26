# Demo Runbook — SAARTHI

> Owner: kv · Status: [x] current (QA-004 rehearsal checklist) · Last updated: 2026-09-08

> **Doctrine: never demo an empty dashboard.** Every screen shows seeded, realistic Indian data (names, 3rd Bn, rosters, leave patterns) from [F09](../features/F09-synthetic-data-generator.md). The demo must survive offline: recorded video fallback on pen drive + two devices, local-run build, hotspot backup. 3-minute script, rehearsed 5× before any jury sees it.

## 1. The 3-minute script (exact beats)

| Beat | Clock | Say (gist) | On screen |
|---|---|---|---|
| Problem | 0:00–0:10 | "In our CAPFs, stress is caught too late — after incidents, not before." Close with **one** statistic from the sourced bank in [research-sih-2026.md](../product/research-sih-2026.md) §7 (say it once, cite it verbally). | Slide 1 (title + statistic) |
| Live demo | 0:10–1:40 | Walk the scripted persona loop (§3) — signals → flag → help → recovery. | Jawan app → counsellor console → commander dashboard, real seeded data |
| Impact | 1:40–2:00 | "The loop closed in days, not after a crisis. And **zero** individual scores can reach command — that's an architectural guarantee, not a promise." (Success-metrics table, [prd.md](../product/prd.md) §4.) | Slide 2 (loop diagram + 0-scores guarantee) |
| Architecture | 2:00–2:20 | "Signals → explainable rules engine → interventions → trust layer. On-device audio, offline-first app, on-prem deployable." (ADR-0001/0002/0003/0005/0006.) | Slide 3 (C4 diagram from [architecture.md](../architecture/architecture.md)) |
| Scale | 2:20–2:30 | "This ran 1,000 personnel with a < 60 s full recompute on this laptop; the rules engine is built for battalion scale." | Slide 4 (scale + what's next) |

Timing is ruthless: 10 s problem → 90 s live → 20 s impact → 20 s architecture → 10 s scale. If a beat runs over, the next presenter starts talking anyway (rehearsed handoff cues).

## 2. Pre-demo checklist (T-minus-30-min)

- [ ] Run `python -m data.gen --seed 42 --personnel 1000` → verify persona "Constable, 34, 3rd Bn" exists and arc is scripted ([F09](../features/F09-synthetic-data-generator.md)); spot-check dashboard cells all have ≥ 5 contributors.
- [ ] All devices charged ≥ 80% (demo laptop + two fallback devices); chargers in bag.
- [ ] Hotspot phone charged + tested (data on, tethering verified).
- [ ] Pen drive carries: recorded demo video, PDF slides, offline installer; **same files emailed** to self + second device.
- [ ] Local-run build verified: `docker compose up` (or documented local run) works with **no internet** — airplane-mode test done this morning, not yesterday.
- [ ] Recorded-video fallback plays on **both** fallback devices.
- [ ] Firewall suite §4 of [test-plan.md](test-plan.md) green on this build (the demo shows the privacy flows — they must pass).
- [ ] Timer on podium; presenter order: problem → demo → impact → architecture → scale.
- [ ] One person carries everything (drive + laptop + hotspot); nothing lives on only one device.

## 3. Persona walkthrough (the 90 seconds, beat by beat)

Scripted persona: **Constable, 34, 3rd Bn** — silent HR signals accumulate, help arrives, loop closes ([F09 §persona](../features/F09-synthetic-data-generator.md)).

1. **(0:10–0:20)** Jawan app, Hindi UI: normal 10-s check-in on a normal day — show how invisible the voluntary part is.
2. **(0:20–0:35)** Commander dashboard: "3rd Bn: elevated fatigue" aggregate (k ≥ 5) — **no names, ever**. This is also where you kill the stigmatization question.
3. **(0:35–0:50)** Counsellor console: Amber flag fires with the explanation — "60 consecutive duty days, 2 cancelled leaves, sleep −30%". Read the factors aloud: explainability is the demo.
4. **(0:50–1:00)** Buddy nudge visible in the app feed; jawan makes a voluntary check-in that contradicts the signals ("I'm fine") — masking flag notes the discrepancy.
5. **(1:00–1:10)** Red → counsellor outreach task with ≤ 24 h SLA; dual-key unmask (counsellor + welfare officer approvals) — point at the audit-log entry appearing live.
6. **(1:10–1:20)** Jawan's phone: who-viewed-my-data shows exactly who opened the record, when, why. **This is the most memorable 15 seconds — do not rush it** ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).
7. **(1:20–1:35)** Roster change (proposed swap, welfare-officer approved) → score trend drops over the following days. Loop closed.
8. **(1:35–1:40)** One-line bridge to impact beat: "the same engine flags the next case before it becomes a statistic."

Rehearsal target: this walkthrough lands inside 90 s every time; if a screen loads slow, narrate while it loads — never dead air.

## 4. Failure modes & fallbacks

| Failure | Fallback | Owner |
|---|---|---|
| API/cloud down | Switch to local-run build (verified offline in checklist) | demo driver |
| Venue network dead | Personal hotspot; if dead too, local build + offline video | hotspot owner |
| Demo device dies | Recorded video on pen drive → play on either fallback device | device owner |
| Laptop dies | USB-C to second device; slides are PDF on drive + email | bag owner |
| Persona data looks wrong / dashboard empty | Re-run the F09 seed script (deterministic, ~minutes); if timing-tight, use recorded video | demo driver |
| Question you can't answer | Say: **"Good question — we'll follow up in writing after this round."** Then actually write it down and send it | any presenter |

Never argue with a jury, never blame the venue, never say "it usually works".

## 5. Rehearsal log (5× rule)

No final-round demo happens until **5 clean rehearsals** are logged here — clean means full 3 minutes, no beat overrun, no fallback used. Run #5 on the actual demo hardware + projector setup.

| # | Date | Hardware | Broke at | Fix applied | Clean? |
|---|---|---|---|---|---|
| 1 | — | bench | — | — | ☐ |
| 2 | — | bench | — | — | ☐ |
| 3 | — | bench + projector | — | — | ☐ |
| 4 | — | demo hardware | — | — | ☐ |
| 5 | — | demo hardware, full setup | — | — | ☐ |

## 6. Post-demo Q&A cheat sheet

Every answer anchors to a written doc — answer in one sentence, then point to the doc. Full preemption table: [research-sih-2026.md](../product/research-sih-2026.md) §7.

| Jury question | One-line answer | Anchor |
|---|---|---|
| "Where is your data?" | PS ships anonymized HR/deployment/wellness datasets; our generator reproduces realistic patterns deterministically today. | [F09](../features/F09-synthetic-data-generator.md) · research §1 |
| "Is it real AI?" | v1 is a clinically grounded rules engine — explainable by construction; ML v2 trains only from counsellor outcome labels. | [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) |
| "What if the model is wrong?" | We say the FP/FN economics out loud: FP = one cup of tea with a counsellor, FN = a life; human sign-off before every intervention. | ADR-0001 · test-plan TC-801 |
| "Privacy under MHA?" | Architectural firewall: individual scores physically cannot reach command; dual-key unmask; append-only audit; break-glass notifies the subject. | [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) |
| "Stigmatization?" | Commander sees aggregates only (k ≥ 5, no names); jawans see who viewed their data. | ADR-0003 · TC-402/404 |
| "Why not an off-the-shelf app?" | Ministry-specific: offline-first, Hindi/low-literacy UI, on-prem air-gappable, no foreign SaaS touches welfare data. | [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [ADR-0006](../architecture/decisions/0006-tech-stack.md) |
| "Will it be used against personnel?" | Zero — that is the design goal; punitive linkage is monitored at 0 in the pilot metrics. | [prd.md](../product/prd.md) §4 |
| "What will you NOT build?" | Explicit out-of-scope answer: no punitive features, no iOS in v1, no ML v2 before labels exist. | research §5 (tactic 10) |
| "Does it scale?" | 1,000-personnel recompute < 60 s measured (TC-701); scaling is onboarding/training, not architecture. | [test-plan.md](test-plan.md) §6 |
| "Who pays after the hackathon?" | The sponsoring org — CRPF/MHA pilot; adoption rides the existing roster app (ADR-0004). | research §5, §7 |

Rule: if the honest answer is "we haven't measured that", say so and log it — an honest gap beats an invented number ([AGENTS.md](../../AGENTS.md) rule 6).

## 7. QA-004 — rehearsal checklist (kv) + recorded-video fallback

The **video file itself** is recorded with risa/tejas (DECK-002 / QA-007). This section is the kv-owned checklist those recordings must satisfy, and the fallback protocol if the live demo dies.

### Rehearsal gate (must all be true before any jury)

- [ ] `cd backend && python -m app.seed` produces DEMO-PERSONA-01; `GET /risk/ps_demo01/explanation` as counsellor returns top-3 factors.
- [ ] `pytest -q` green on the demo laptop, including `test_firewall.py` (ADR-0003 must-pass).
- [ ] `python -m app.ml.harness` exits 0 (persona arc diffs empty).
- [ ] Commander login `commander.3bn` / `saarthi` shows `/aggregates/unit/3BN` with no names.
- [ ] Who-viewed on `jawan.demo` shows the counsellor read after a console open — the 15-second moment.
- [ ] `docker compose up` (or `uvicorn` local) still serves after airplane mode on the laptop.
- [ ] Five rows filled in §5 rehearsal log, last one on the actual projector.

### Recorded-video fallback spec (what tejas records)

| Shot | Duration | Must show | Must not show |
|---|---|---|---|
| 1. Jawan check-in (Hindi) | 10 s | 10-second check-in, `instr.not_diagnosis` visible | anyone else's data |
| 2. Commander aggregate | 15 s | "3rd Bn" elevated fatigue, k ≥ 5, **no names** | any personnel_id, any score |
| 3. Counsellor explanation | 20 s | top-3 factors read aloud | raw journal |
| 4. Masking + Red SLA | 15 s | "I'm fine" vs duty/leave; outreach ≤ 24 h | disciplinary language |
| 5. Dual-key + who-viewed | 20 s | two approvals; jawan phone receipt | the unmasked name on a commander screen |
| 6. Roster swap + trend down | 10 s | proposal + load delta | a score on the commander view |

Export: 1080p mp4, < 100 MB, **no internet required to play**. Copies: pen drive, emailed to kv + risa, second device. Filename: `SAARTHI-demo-fallback-YYYYMMDD.mp4`.

If live demo fails: presenter says one sentence ("we'll play the recorded walkthrough") and hits play. Never debug on stage.

### Blockers logged 2026-09-08

- APP-001…010 (neel) — mobile/web UI not in this backend PR; API + seed are. Live app screens wait on neel.
- DECK-001 (risa) — official-template deck not built.
- QA-007 / DECK-002 — fallback video not yet recorded.

Backend-only rehearsal (API + OpenAPI + seeded persona) **can** start now. Full 3-minute jury demo cannot be marked clean until the three blockers move.
