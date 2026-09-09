# Clinical Instruments — Validated Screeners in SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> Ground rule: **validated instruments only, never invented questions** (FR-02, [PRD](../product/prd.md)). Every instrument ships with the visible label *"reflection support — not diagnosis"* (§5).

## 1. The instrument set at a glance

| Instrument | Measures | Items | Score | Band anchors | Why chosen |
|---|---|---|---|---|---|
| **PHQ-9** (Kroenke, Spitzer & Williams 2001) | Depressive symptoms | 9 | 0–27 | 5/10/15/20 = mild/moderate/mod-severe/severe; ≥10 = conventional positive screen | Gold-standard screener, brief, widely translated incl. Hindi; item 9 supports safety routing |
| **GAD-7** (Spitzer et al. 2006) | Anxiety symptoms | 7 | 0–21 | 5/10/15 = mild/moderate/severe; ≥10 = positive screen | Designed for repeat administration — enables trend measurement, the system's core value |
| **PSS-10** (Cohen, Kamarck & Mermelstein 1983) | *Perceived* stress, past month | 10 | 0–40 | No clinical cutoff — population norms + personal trend | Stress here is situational (roster, separation); perceived-stress framing fits welfare monitoring |
| **MBI** (Maslach & Jackson 1981) | Burnout: emotional exhaustion, depersonalization, personal accomplishment | 22 | 3 subscales, each rated 0–6 | Occupational norms; subscales **never summed** | Burnout is the PS's named target; ICD-11 (QD85) recognises it as an occupational phenomenon |
| **ISI** (Bastien, Vallières & Morin 2001) | Insomnia severity | 7 | 0–28 | 0–7 none · 8–14 subthreshold · 15–21 moderate · 22–28 severe; ≥15 = clinically significant | Sleep disruption is a core, roster-linked signal in duty-rotated forces |
| **PCL-5** (Weathers et al. 2013) | PTSD symptoms (DSM-5) | 20 | 0–80 | Provisional screening cutoff ≈33 (31–33 reported) | Group trauma exposure (FR-08) makes trauma screening necessary; public domain |

The set is deliberate: six brief instruments, all valid for repeat administration on a low-end Android screen (NFR-04). Full monthly battery stays under ~5 minutes — a reasoned estimate checked against item counts above — because a battery nobody finishes honestly is worse than a shorter one.

## 2. Per-instrument notes

### PHQ-9 — depression
Nine items mirroring DSM-IV MDD criteria (Kroenke et al. 2001). Bands: 0–4 minimal, 5–9 mild, 10–14 moderate, 15–19 moderately severe, 20–27 severe. **Item 9 (thoughts of self-harm) triggers the human safety protocol** — counsellor/Tele-MANAS 14416 routing, never an app-only response. No built-in validity scale; response-pattern defences (§4) apply. Hindi: validated Hindi versions are in published use in Indian research and practice; confirm the exact version with the clinical advisor before shipping (owner ML-001).

### GAD-7 — anxiety
Seven items (Spitzer et al. 2006), bands at 5/10/15, ≥10 positive screen. Chosen because it was built to be short enough for repeat use — which is what makes per-person trend curves possible ([model-explainer.md](model-explainer.md) §3). Same "confirm the Hindi version with the advisor" caveat.

### PSS-10 — perceived stress
Ten items about the last month; 0–40 with items 4, 5, 7, 8 reverse-scored (Cohen et al. 1983). **No clinical cutoff**: interpreted against population norms and the person's own trajectory — exactly how the engine uses it (per-person baselines). Hindi adaptations exist in the literature; wording validated with the advisor.

### Maslach Burnout Inventory — burnout
22 items in three subscales — emotional exhaustion (9), depersonalization (5), personal accomplishment (8) — each on a 0–6 frequency scale (Maslach & Jackson 1981). Subscale scores are **never summed**; interpretation is against occupational norms. ICD-11 classifies burnout as an occupational phenomenon (QD85), which reinforces the welfare-not-clinical framing. **Licensing note: MBI is a paid, licensed instrument (Mind Garden).** Licence acquisition is a v1 gate — else it is deferred; a paraphrased clone would violate the validated-instruments-only rule.

### Insomnia Severity Index — sleep
Seven items, 0–28 (Bastien et al. 2001); ≥15 conventionally flags clinically significant insomnia. Fits the signal model directly: sleep is triangulated from self-report, roster-derived circadian disruption score, and (optionally, low weight) on-device voice features ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)).

### PCL-5 — trauma
Twenty DSM-5 PTSD symptom items, 0–80; provisional screening cutoff ≈33 (National Center for PTSD guidance; Blevins et al. 2015). **Public domain** — distributed by the National Center for PTSD without permission requirement. Deployed after group-trauma exposure events (FR-08): a high score in an exposed unit is welfare-relevant context for the counsellor, not a standalone trigger.

## 3. Translation AND adaptation — Hindi and regional languages

A literal translation of a Western scale scores wrong: idiom, literacy level and cultural framing distort item meaning, so a straight word-for-word translation is not used. Adaptation follows published practice (Beaton et al. 2000; Wild et al. 2005):

1. **Forward translation** into Hindi by two independent bilinguals — one clinical, one language-native.
2. **Synthesis** into a single version, then **back-translation** by a blinded third translator.
3. **Expert-committee review** — clinical advisor + language expert reconcile all versions item by item.
4. **Pilot testing** with target-population personnel; comprehension and response distributions reviewed before rollout.

Regional languages (PS: "Hindi + regional languages later", NFR-04) follow the same pipeline. Every adapted item maps back to its original item ID for audit, and the English instrument stays authoritative for scoring bands until an adapted version is itself validated — bands are never re-invented per language.

## 4. Guarding against faked self-reports

Under-reporting is the norm in uniformed forces — the design assumes it and triangulates three sources ([model-explainer.md](model-explainer.md) §2). Instrument-side defences:

- **Social-desirability catch items** inside each instrument, in the tradition of the MMPI L-scale (Hathaway & McKinley) and the Marlowe-Crowne Social Desirability Scale (Crowne & Marlowe 1960): statements nearly everyone endorses ("I have never been late for duty") that reveal desirability bias when maximally endorsed.
- **Response-pattern detection** (Meade & Craig 2012): straight-lining (identical answers across items), completion implausibly fast to have read the questions, all-max / alternating responses.
- A flagged pattern **lowers the self-report's weight and raises the discrepancy (masking) flag** (FR-07): the faking is the finding, not a data-quality problem — someone hiding distress in a high-stigma organisation is a *higher* risk, so the response is support, not penalty.

## 5. "Reflection support, not diagnosis"

Every instrument screen and check-in carries the visible bilingual label: **यह निदान नहीं, आत्म-चिंतन का सहारा है — reflection support, not diagnosis** (i18n key `instr.not_diagnosis`, defined in [F02](../features/F02-jawan-app.md)). Screeners indicate *where reflection and support may help*; a clinical diagnosis requires a qualified professional's assessment. Hard boundaries: the system never outputs a diagnosis, never gates duties on an instrument score, and routes Red/Critical states to humans ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md), [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md)).

## 6. Cadence — daily 10-second check-in vs monthly full instrument

- **Monthly full instrument** gives *anchors*: validated scores with population-level meaning, comparable across months.
- **Daily 10-second check-in** gives *trajectory*: survey burden is real — long instruments breed careless responses (Meade & Craig 2012) — so high-frequency measurement must cost one tap (emoji/slider, FR-02, offline-first per [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md)).
- Together: **velocity + anchor**. The daily check-in detects a rapid slide between monthly anchors; the monthly instrument recalibrates and validates the trend. This pairing is a reasoned design trade-off, not an evidence-backed optimum — the pilot measures it ([PRD §4](../product/prd.md)).

A boundary keeps the two honest: the daily check-in is **not** a mini-instrument — it carries no validated score and never maps to a diagnostic band; it exists to feed per-person baselines and the discrepancy check (FR-07). Its items are still designed with the advisor and carry the same reflection-support label; if a daily-scale need emerges later, it gets validated first, deployed second — the same rule as every instrument in §1.

## 7. Implementation status (as of 2026-09-09)

Sections 1–6 are the design. This section is what is in the repository, read off
`/Users/ns/code/sih-hackathon-26/web/packages/instruments/src/{bank.ts,scoring.ts,types.ts}` and
`web/apps/jawan/app/(tabs)/welfare/instrument/`. Where the two disagree, the code is the fact and §1–6 is the
intent.

### 7.1 The shipped bank is four instruments, not six

`BANK` is **PHQ-9, GAD-7, PSS-10, ISI**. **MBI and PCL-5 are not implemented** — no items, no scoring, no
entry in the bank — and the backend's `INSTRUMENTS` tuple in `app/api/routers/self_service.py` matches at
four. §1 lists them because the clinical case for them is unchanged; MBI in particular is blocked on the
paid Mind Garden licence already flagged in §2, and PCL-5 (public domain) is simply unbuilt.

### 7.2 Which instruments ship item text, and why

| Instrument | Item text ships? | `licence` | Why |
|---|---|---|---|
| PHQ-9 | Yes, all 9 published stems | `reproducible` | Pfizer released the PHQ/GAD family for reproduction **without permission required**, so the stems ship verbatim |
| GAD-7 | Yes, all 7 published stems | `reproducible` | same PHQ/GAD release |
| PSS-10 | Yes, all 10 published stems, items 4/5/7/8 flagged `reverse` | `reproducible` | Cohen, Kamarck & Mermelstein (1983) — free for research and educational use |
| **ISI** | **No — `items: []`** | `licence_pending` | The items are **copyrighted** (Bastien, Vallières & Morin 2001). Scoring, the four bands and the flow are all implemented; the item text is withheld until a licence is in place |

This is the direct consequence of §1's ground rule. A paraphrased ISI would be an **invented questionnaire
wearing a validated instrument's name and bands** — worse than shipping nothing, because it would score
against cutoffs derived from wording it no longer uses. So the code refuses the paraphrase and says so in
three places at once: `ISI.items` is empty, `ISI.licenceNote` states the reason in the source file,
and `answerable()` filters on `licence === "reproducible" && items.length > 0`. The app follows: the picker
at `/welfare/instrument` renders ISI as a disabled card carrying `instrument.licencePending`
("Not available yet — the licence for this questionnaire is still being arranged."), and the run page at
`/welfare/instrument/ISI` early-returns the same message rather than starting a flow with no questions.
`instruments.test.ts` asserts it — *"a licensed instrument ships no item text at all"* and *"answerable()
excludes anything we cannot legally present"*.

The honest framing for a jury: **the ISI gap is the rule working, not a missing feature.** Sleep is still
measured — the daily check-in carries self-reported sleep hours, and PHQ-9 item 3 is a sleep item — it is
just not measured by a validated insomnia instrument until the licence exists.

### 7.3 Every Hindi rendering is `adaptation: "review_pending"`

All four instruments carry `adaptation: "review_pending"`, because **the §3 pipeline has not been run** —
no forward translation by two independent bilinguals, no blinded back-translation, no expert-committee
reconciliation, no pilot. The `hi` strings in `bank.ts` are a working romanised rendering for usability
testing, not a validated adaptation, and `instruments.test.ts` has a test whose entire job is to fail if
anyone marks one `adapted` before the review happens (*"no Hindi rendering is claimed as adapted before the
review runs"*).

Two consequences are enforced rather than promised:

- **English stays authoritative for scoring.** Bands are attached to the instrument, not to a locale; there
  is no per-language band table to drift.
- **The app says so on screen.** The instrument picker renders `instrument.translationPending` on any card
  whose `adaptation` is `review_pending` **when the locale is `hi`** — en: *"The Hindi wording is still under
  clinical review. English is authoritative for scoring."* · hi: *"Hindi shabdon ki clinical jaanch chal rahi
  hai. Score ke liye English hi maanya hai."* A person reading the Hindi flow is told, in Hindi, that the
  Hindi is provisional. Note the current gap: the notice appears on the **picker**, not on each question
  screen inside the run.

### 7.4 The two validity probes are genuine, separate, and never scored

`VALIDITY_ITEMS` are two real **Marlowe-Crowne Social Desirability Scale** items (Crowne & Marlowe 1960) —
`MC-01` *"I have never intensely disliked anyone."* and `MC-02` *"I am always courteous, even to people who
are disagreeable."* — not invented catch items. §4's design is implemented exactly:

- They ride at the **end** of every instrument on their own 0–4 agreement scale (`AGREE5`), while the
  instrument's own items keep their published scale. The run page marks them with
  `instrument.validity.note` ("Two of the statements check answering style, not wellbeing.") instead of the
  instrument's recall window, so the person is not misled about what is being asked.
- They are **excluded from the instrument total**: `scoreInstrument` sums `instrument.items` only, and
  `instrument.validityItems` is a separate array. A test asserts *"the probes never move the instrument
  score"*.
- `validity_fail` fires when **both** probes are answered at the scale maximum (`>= 4` on AGREE5).

Response-pattern detection is in `scoring.ts` with these thresholds:

| Flag | Condition as implemented |
|---|---|
| `straight_lining` | at least 3 scored items answered **and** every scored answer identical |
| `too_fast` | elapsed answering time < `answered × 1600 ms` (`MIN_MS_PER_ITEM = 1600`) — about 1.6 s per item, already implausibly fast for read-and-consider |
| `all_max` | at least 3 scored items answered **and** every scored answer at the scale maximum |
| `validity_fail` | both Marlowe-Crowne probes endorsed at the maximum |

Two details worth knowing before quoting the numbers: the elapsed clock accumulates only time spent
*answering* (it advances on each answer and each Next, and is persisted with the draft so an interrupted run
resumes with its real elapsed time), and all four flags travel to the server as booleans on the queued
`instrument` row. **Per-item responses never leave the device**: the payload is the total, the four flags,
`recorded_at`, and — for PHQ-9 only — the raw `item_9` value, which is there precisely because it routes a
human (§7.5). Per §4, a flagged pattern lowers the
self-report's weight and raises the discrepancy flag (FR-07); it is never treated as misconduct.

### 7.5 PHQ-9 item 9 routes to a human, never to an app-only response

`PHQ9.safetyItemIndex = 9`; `scoreInstrument` lifts that item's raw value onto the result as `item_9`, and
`needsSafetyProtocol()` returns true on **any endorsement at all** (`item_9 >= 1`) — not at a band, not at a
threshold. When it returns true the run page replaces the entire flow with a safety screen. It is
non-dismissable by construction: the branch renders no exit link, no back button, no "skip" and no
"continue" — there is no way onward through the questionnaire from it. It is `aria-live="assertive"`, and it
carries

- a direct `tel:14416` dial link — Tele-MANAS (`instrument.safety.call`);
- **"Ask a counsellor to contact me"** (`instrument.safety.counsellor`), which calls `drainNow()` so the
  queued row carrying `item_9` is sent immediately rather than waiting for the next opportunistic drain —
  the one queued row in the product that should not sit on a device;
- the helpline again in the footer.

No score, no band and no interpretation is shown — on this screen or on the normal completion screen, which
says `instrument.noBand` ("No score band is shown. Your own trend is what matters."). The app's answer to a
self-harm endorsement is a person and a phone number, which is the whole of §5's boundary and
[mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md)'s requirement.
`instruments.test.ts` asserts that any endorsement triggers it, that a zero does not, and that instruments
without a safety item never carry `item_9` at all.

### 7.6 Known gaps in this feature

- **MBI and PCL-5 unbuilt** (§7.1); the §1 table is aspirational for those two rows.
- **ISI item text licence-gated** (§7.2) — deliberate, and the correct behaviour until a licence exists.
- **No Hindi adaptation review has run** (§7.3); the on-screen notice covers the picker, not each question.
- **`instr.not_diagnosis`, cited in §5 as "defined in F02", is a server-side key** in
  `backend/app/i18n.py`, not a key in the web dictionary. The web screens render the same sentence from
  `screen.disclaimer`. The Devanagari value promised in §5
  ("यह निदान नहीं, आत्म-चिंतन का सहारा है") exists only on the server key; the app's `hi` string is
  romanised ("Ye aatm-chintan ka sahara hai, nidan nahi.") — see [F02](../features/F02-jawan-app.md) on the
  romanised-Hindi convention.
- **No clinician has signed anything off.** Every "confirm the Hindi version with the advisor" caveat in §2
  is still open (owner ML-001).

## Sources

- Kroenke K, Spitzer RL, Williams JBW (2001) — PHQ-9, J Gen Intern Med 16(9):606–613.
- Spitzer RL et al. (2006) — GAD-7, Arch Intern Med 166(10):1092–1097.
- Cohen S, Kamarck T, Mermelstein R (1983) — PSS, J Health Soc Behav 24(4):385–396.
- Maslach C, Jackson SE (1981) — MBI, Journal of Occupational Behaviour 2(2):99–113 · WHO ICD-11 QD85 (burn-out).
- Bastien CH, Vallières A, Morin CM (2001) — ISI, Sleep Medicine 2(4):297–307.
- Weathers FW et al. (2013) — PCL-5, National Center for PTSD · Blevins CA et al. (2015) — PCL-5 psychometrics, J Anxiety Disord.
- Crowne DP, Marlowe D (1960) — social desirability, J Consulting Psychology 24:349–354 · Meade AW, Craig SB (2012) — careless responding, J Business & Psychology 27:437–452.
- Beaton DE et al. (2000) — cross-cultural adaptation guidelines, Spine 25(24):3186–3191.
