# Usability Testing Protocol — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> How-to doc (Diátaxis: quality). Governs all moderated sessions before the pilot. Feeds [F02](../features/F02-jawan-app.md) fixes and R2 "usability" scoring. Companions: [design.md](../architecture/design/design.md) · [usability ADR](../architecture/decisions/0005-offline-first-low-end-android.md).

## 1. Why this protocol exists

Our users are uniformed personnel with **mixed literacy, Hindi-first usage, low-end Android phones, and bad connectivity** — and a cultural guard against anything that smells like a therapy app. We test with **uniformed-force-adjacent users** (ex-servicemen, home guards, NCC seniors, police-family members) because active CRPF access is limited; they approximate the literacy, language, and cultural frame. Findings transfer as *risk signals*, not proof.

## 2. Sessions & participants

- 8–10 moderated sessions, 45 minutes each, in Hinglish (moderator script provided in both languages).
- One participant per session; observe pairs only for commander/welfare-officer roles.
- Mix: ≥ 50% participants with low or intermediate literacy (self-reported, no literacy tests on record); ≥ 3 participants on devices ≤ 2 GB RAM / Android 8–9.
- Think-aloud adapted for low literacy: **observation over verbalisation** — success is measured by what they do, not what they can narrate; moderator asks "what would you tap next?" instead of "why?".
- Consent: recorded with permission; no participant named in reports; no distress-inducing content; any participant may stop at any time.

## 3. Task list per persona

**Jawan app (core, ~25 min):** open the app and find tomorrow's duty · apply for leave and check status · find the pay slip · complete the 10-second check-in (`checkin.prompt` "Aaj kaisa laga?") · answer one PHQ-9 question · open "who viewed my data" and say who accessed the record · withdraw one consent · go offline and complete a check-in.

**Welfare officer console:** open the case queue · read one evidence card and name its top factors · propose a roster swap · log an intervention outcome.

**Counsellor console:** find a Red-tier case · request dual-key unmask (with moderator as second key) · write a session note · view the before/after trend.

**Commander dashboard:** read the unit heatmap · find the morale index · run the what-if simulator · **negative task:** attempt to view an individual's score — must be impossible ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).

## 4. Mixed-literacy protocol

- **Icon comprehension checks:** after each state screen, ask the participant to name what the leaf / sun / hand-heart / phone icons mean, unprompted. Target: ≥ 4 of 5 participants identify each icon's meaning without the text label. If an icon fails, the text label is doing the work — fix the icon.
- **No-colour-alone check:** verify the welfare ladder is distinguishable with colour perception disabled (deuteranopia/protanopia simulation) — icons + lightness must carry it ([design.md §2](../architecture/design/design.md)).
- **Voice-input tests:** complete the check-in **entirely by voice**, keyboard never opened; keep-or-rerecord flow understood without instruction; Hindi transcription acceptable to the participant.
- **Devanagari rendering check:** no matra clipping at any text size (no fixed-height containers); 200% zoom survival on consoles.

## 5. Low-end device matrix

| Device class | Spec we test on | Verifies |
|---|---|---|
| Low-end floor | Android 8 (API 26), ~2 GB RAM, small screen | Install, cold start, check-in, offline queue |
| Mid-range common | Android 11–13, 4 GB | Full flow, voice input, sync |
| Console machine | Modest laptop | Counsellor/welfare/commander consoles at 1366×768 |

Plus: throttled network (2G-class) for every sync scenario. Devices owned by the team; no participant-device borrowing. iOS is out of scope ([ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md)).

## 6. Offline scenarios

1. Airplane mode before opening the app → complete a check-in → confirm the sync pill says data is saved, will send.
2. Network loss mid-check-in → no data loss, no red error styling, recovery copy in the welfare register ("Sync nahi hua. Data safe hai, dobara try karenge").
3. Reconnect → queued check-ins sync without user action; participant does not need to understand anything about sync.

## 7. Success criteria (per task)

- Completion: jawan core tasks ≥ 80% unassisted; console tasks ≥ 70% (targets — reasoned, not evidence).
- Time: 10-second check-in genuinely ≤ 10–15 s on the low-end device.
- Icon comprehension: per §4 thresholds.
- Zero task where the participant must read English to proceed.
- Offline scenarios: 100% data-retention — any lost check-in is a stop-ship defect ([FR-04](../features/F02-jawan-app.md)).

## 8. The ADR-0004 check — "does this feel like a therapy app?"

The decisive test. After tasks, a perception battery (asked in Hinglish, answers paraphrased in the log):

1. "In one word, what is this app?" — **pass** if roster/leave/duty-family answers dominate; **fail** if "mental health", "therapy", "doctor app" dominate free recall.
2. "Who is this app for?" — pass: the jawan, for duty and family; fail: for doctors or officers to watch personnel.
3. "Would you install it if a friend in the force had it?" (yes/no + why).
4. "Does it feel like help or like monitoring?" (forced choice).
5. "Would you check in with your mates standing nearby?" (the stigma probe).

Fail on items 1 or 2 → adoption framing is broken → revisit [adoption-strategy.md](../product/adoption-strategy.md) and onboarding copy before any further usability work. The roster screens must be the remembered home of the app, with check-in as a calm resident — never the headline.

## 9. Findings → fixes

- Log per session: task, path taken, assist level (none/verbal/physical), verbatim quote, severity (blocker / major / minor).
- Blockers and ADR-0004 failures enter the current sprint; majors before pilot; minors batched.
- Retest gate: any changed flow re-runs its failed tasks with ≥ 3 fresh participants before the next milestone. Results summarised into [test-plan.md](test-plan.md) traceability.

## Links

[ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [prd.md §3 NFR-04](../product/prd.md#3-non-functional-requirements) · [F02](../features/F02-jawan-app.md) · [test-plan.md](test-plan.md)
