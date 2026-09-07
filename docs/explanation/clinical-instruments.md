# Clinical Instruments — Validated Screeners in SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
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

## Sources

- Kroenke K, Spitzer RL, Williams JBW (2001) — PHQ-9, J Gen Intern Med 16(9):606–613.
- Spitzer RL et al. (2006) — GAD-7, Arch Intern Med 166(10):1092–1097.
- Cohen S, Kamarck T, Mermelstein R (1983) — PSS, J Health Soc Behav 24(4):385–396.
- Maslach C, Jackson SE (1981) — MBI, Journal of Occupational Behaviour 2(2):99–113 · WHO ICD-11 QD85 (burn-out).
- Bastien CH, Vallières A, Morin CM (2001) — ISI, Sleep Medicine 2(4):297–307.
- Weathers FW et al. (2013) — PCL-5, National Center for PTSD · Blevins CA et al. (2015) — PCL-5 psychometrics, J Anxiety Disord.
- Crowne DP, Marlowe D (1960) — social desirability, J Consulting Psychology 24:349–354 · Meade AW, Craig SB (2012) — careless responding, J Business & Psychology 27:437–452.
- Beaton DE et al. (2000) — cross-cultural adaptation guidelines, Spine 25(24):3186–3191.
