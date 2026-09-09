# Usability Testing Protocol — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-09
> How-to doc (Diátaxis: quality). Governs all moderated sessions before the pilot. Feeds [F02](../features/F02-jawan-app.md) fixes and R2 "usability" scoring. Companions: [design.md](../architecture/design/design.md) · [usability ADR](../architecture/decisions/0005-offline-first-low-end-android.md).
>
> **Run order:** recruit §2.1 → screen §2.3 → prepare [Appendix A](#appendix-a--how-to-run-a-session-in-20-minutes) → run §10 (script) over §11 (tasks) → score §12 → check §13 → log §15 → triage §9.1 → file §9.2. §14 (icon + voice review) is a design review that must be **closed before session 1** — it lists defects that would otherwise confound the results.
> §§1–8 are the standing protocol (unchanged); §§9.1–15 and the appendix are the runnable instrument added by UX-001 (2026-09-09).
>
> **Citation convention.** `design.md §N` and `prd.md §N` point at that file's numbered `##` heading. `F02 §N` / `F03 §N` point at the numbered **screen** N in that feature doc's *User-visible behavior (screen by screen)* list — F02 §1 Home · §2 Check-in sheet · §3 Monthly instrument · §4 My trend · §5 Consent panel · §6 Who viewed my data · §7 Battle buddy · §8 Unit pulse · §9 Settings; F03 §1 Voice check-in capture. Those feature docs have no numbered headings, so read the § there as a screen number.

## 1. Why this protocol exists

Our users are uniformed personnel with **mixed literacy, Hindi-first usage, low-end Android phones, and bad connectivity** — and a cultural guard against anything that smells like a therapy app. We test with **uniformed-force-adjacent users** (ex-servicemen, home guards, NCC seniors, police-family members) because active CRPF access is limited; they approximate the literacy, language, and cultural frame. Findings transfer as *risk signals*, not proof.

## 2. Sessions & participants

- 8–10 moderated sessions, 45 minutes each, in Hinglish (moderator script provided in both languages).
- One participant per session; observe pairs only for commander/welfare-officer roles.
- Mix: ≥ 50% participants with low or intermediate literacy (self-reported, no literacy tests on record); ≥ 3 participants on devices ≤ 2 GB RAM / Android 8–9.
- Think-aloud adapted for low literacy: **observation over verbalisation** — success is measured by what they do, not what they can narrate; moderator asks "what would you tap next?" instead of "why?".
- Consent: recorded with permission; no participant named in reports; no distress-inducing content; any participant may stop at any time.

### 2.1 Participant matrix — target segments, proxies, n per segment

| # | Target segment (who we actually need) | What only they can tell us | n | Proxy we can realistically recruit for an SIH prototype | The gap the proxy leaves |
|---|---|---|---|---|---|
| 1 | **Constable / jawan — low literacy, Hindi-first** ([personas §1](../product/personas.md), primary) | whether the 10-second loop survives a real duty day; whether the roster framing lands | **4** | campus security guards, mess/housekeeping staff, drivers — Hindi-first, low-end Android, shift work under a hierarchical employer | no ACR/career exposure; no unit lines; no deployment connectivity |
| 2 | **Head constable / havildar** — supervises, still a user | whether a supervisor uses it themselves or only pushes it downward | **2** | shift supervisor, campus security head, home guard | the "push it downward" dynamic is institution-specific |
| 3 | **JCO / SI** — the buddy-escalation contact ([F02 §7](../features/F02-jawan-app.md)) | whether a JCO would actually answer a buddy `sos` at 2 a.m. | **1** | ex-serviceman, NCC ANO, hostel warden | no real duty obligation attached to the answer |
| 4 | **Counsellor** | whether an evidence card is actionable in one sitting (personas §2) | **1** | campus counsellor / clinical-psychology postgraduate | no force caseload, no dual-key experience |
| 5 | **Welfare officer** | whether a roster-swap proposal is usable without becoming enforcement | **1** | NSS/NCC officer, hostel warden, HR welfare staff | no CRPF welfare machinery behind the action |
| 6 | **Commander / CO** | whether aggregates-without-individuals are accepted, or the firewall gets fought | **1** | senior faculty/HoD, NCC CO, retired officer | the loss-of-control reaction *is* the question, and a proxy cannot supply it |
| — | **retest pool** ([§9](#9-findings--fixes) gate) | — | **≥ 3 fresh** | drawn from segment 1 | — |

Total **10 sessions** + a fresh retest pool, consistent with §2's 8–10. Composition rules on top of §2: ≥ 5 of the 10 from segments 1–2 · ≥ 3 on a §5 floor device · ≥ 5 sessions run in Hindi · no participant runs twice in one round · the retest pool must be **fresh** people, never the ones who already saw the flow.

**Recruitment reality (state this plainly, including in the deck):**
- Serving CRPF personnel are **not** recruitable for a student prototype without unit/MHA permission. We do not have it, and no artefact may imply we do.
- No session runs inside a workplace, a unit, or within sight of an employer — that voids it (§13 C).
- **No payment.** Reimburse travel, offer tea, nothing more. Paying for opinions on a product whose central question is *"would you answer honestly under pressure?"* buys precisely the answer we are trying not to get.
- Recruit through personal networks, at most one degree from the moderator, and **never through the participant's employer**.

### 2.2 What a proxy participant cannot tell us

A campus guard is a sound proxy for **literacy, language, device class and shift-work hierarchy**. They are not a proxy for the following, and no session count fixes it:

1. **Whether a serving jawan believes the privacy claim under real career risk.** The fear in personas §1 is specific — "a score becoming a file note", an ACR entry. A proxy has no ACR. Every trust result in §12 is therefore an **upper bound**; real belief will be lower, not higher.
2. **Stigma at true base rate.** Testing one-to-one in a quiet room removes the exact variable §8's stigma probe is about (mates within earshot in unit lines). §14.3 layer 3 is a partial substitute and is labelled as partial.
3. **Whether the roster data is right.** A proxy has no duty roster to check the app against, so T2 measures findability, never correctness. Correctness needs the HRMS integration and real users.
4. **Whether the loop survives 47 consecutive duty days.** Fatigue, habituation and drop-off are longitudinal. Adoption is a **pilot** measure ([adoption-strategy.md](../product/adoption-strategy.md)), never a 45-minute lab measure.
5. **Whether command actually refrains from asking.** [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) guarantees against a *technical* leak. The social leak — "sahab asked me what I answered" — is organisational behaviour and no usability session touches it.
6. **Real deployment connectivity.** §5's throttling approximates a bad network; it does not reproduce a week without one.
7. **Whether the register lands as ours rather than theirs.** A proxy can tell us a sentence is unclear. Only a serving member can tell us it sounds like an outsider wrote it.

Consequence for the log: every finding row carries a **Confidence** value — `proxy` (default this round), `near-target` (ex-CAPF, home guard, serving state police), `target` (serving CRPF; expect **zero** this round). A `proxy` finding is a **risk signal that justifies a design change** — never evidence that the design is right (§1; AGENTS.md rule 7).

### 2.3 Screener — five questions, asked when booking, never on the day

1. What phone do you use? *(need: Android; ideally ≤ 4 GB RAM / Android 8–11 — §5)*
2. Which language do you prefer on your phone?  *(need ≥ 5 Hindi sessions)*
3. When something is written on your phone, is it easier for you in Devanagari, in English letters, or would you rather someone read it out? *(the romanisation question — §14.3. Ask it plainly and without embarrassment; it is not a literacy test and nothing is scored.)*
4. Do you work in shifts, with a duty roster? *(segment 1–2 fit)*
5. Is there anyone whose permission you would need in order to talk to me? *(if **yes** → do not book. That relationship is the coercion risk — §13.)*

No literacy test is administered or recorded (§2).

## 3. Task list per persona

**Jawan app (core, ~25 min):** open the app and find tomorrow's duty · apply for leave and check status · find the pay slip · complete the 10-second check-in (`home.checkin.title` "Aaj kaisa laga? (10 second)") · answer one PHQ-9 question · open "who viewed my data" and say who accessed the record · withdraw one consent · go offline and complete a check-in.

**Welfare officer console:** open the case queue · read one evidence card and name its top factors · propose a roster swap · log an intervention outcome.

**Counsellor console:** find a Red-tier case · request dual-key unmask (with moderator as second key) · write a session note · view the before/after trend.

**Commander dashboard:** read the unit heatmap · find the morale index · run the what-if simulator · **negative task:** attempt to view an individual's score — must be impossible ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).

> §3 is the **coverage map** — everything the product must eventually be testable on. [§11](#11-the-six-measured-tasks-runnable-core) is the **runnable subset**: six tasks with end events, tap budgets and hard time budgets, which is what an actual 20–45 minute session executes. Console tasks stay in §3 until those apps exist — `web/apps/` contains only `jawan` today.

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

### 9.1 Severity rubric — 1 to 4, with the fix-by rule

The three words above (blocker / major / minor) are the shorthand for S1 / S2 / S4. The scale below is the one written into the log.

| Sev | Shorthand | Definition — any one of these | Fix-by rule (hard) | Gate |
|---|---|---|---|---|
| **S1** | blocker / stop-ship | (a) any data loss, including one queued check-in; (b) a privacy claim shown to be false, **or** shown to be believed-falsely — a trust answer that moves *away* from the architecture (§12); (c) any individual-level leak toward command ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)); (d) a coercion signal traced to a product feature (§13 C); (e) participant distress caused by a screen or a string | **Testing stops.** Fixed and retested before the next session; no further sessions run on the broken build | blocks merge **and** blocks demo — same register as the [test-plan.md](test-plan.md) §4 firewall suite |
| **S2** | major | task fails unassisted for **≥ 2** participants in the run; or exceeds its time budget by > 2×; or a §4 icon-comprehension threshold misses; or withdrawal is deeper than granting | before the internal-round gate (**PM-002, 2026-09-18**); if it sits on the demo path, before DECK-001 screenshots | blocks the owning `APP-*` task's Definition of Done |
| **S3** | moderate | one participant fails or needs assist ≥ 2; a string is misread but recovered; an affordance with no action behind it; a finding that points at the environment rather than the product | batched into the next change to that flow; closed before the pilot | no gate; listed in the owning F-doc's DoD |
| **S4** | minor | cosmetic, wording polish, a nit with no measured behaviour behind it | backlog; may be closed by a one-line doc note | none |

- **Escalation by frequency:** an S3 observed in **three different sessions** becomes S2 automatically. Frequency is evidence even when a single instance is not.
- **De-escalation** is done only by neel, in the review, with the reason written into the row. A note-taker never lowers a severity — leaving it blank is correct and expected.

### 9.2 Where a finding gets filed

| Screen / concern | Owning board task | Doc updated in the same PR (AGENTS.md rule 1) |
|---|---|---|
| check-in sheet, emoji row, slider, instrument flow | **APP-003** | [F02](../features/F02-jawan-app.md) §2–3 |
| roster / leave / pay-slip home, service cards, settings + language switch | **APP-002** | F02 §1, §9 |
| offline queue, sync pill, service worker, cold start | **APP-001** | F02 States · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) |
| consent panel, withdrawal depth, silent withdrawal | **APP-004** | F02 §5 · F08 |
| who-viewed-my-data receipts | **APP-005** | F02 §6 · [design.md §5](../architecture/design/design.md) |
| mic, waveform, voice privacy line, recorded prompts | **APP-006** | [F03](../features/F03-on-device-signals.md) §1 |
| icons, care-state chips, tokens, contrast, type | **UX-002** | design.md §2 / §3 / §9 |
| counsellor / commander console findings | APP-007 · APP-008 · APP-010 | F06 / F07 |
| anything that proves a privacy claim false | **PRIV-003** + the S1 rule above | F08 · [security-model.md](../compliance/security-model.md) |

Board rows belong to kv (AGENTS.md rule 3) — **never edit `executable/board.md`.** Send kv the finding ID, the proposed owning task and the severity; kv adds or amends the row. Every S1 additionally gets a `TC-4xx` case in [test-plan.md](test-plan.md) so the fix is regression-covered rather than merely fixed.

## 10. Moderator script (verbatim — English + Hindi)

Read these lines as written. They are **spoken** moderator lines, not product strings, so they carry no i18n keys; every *product* string proposed anywhere in this document is given as `key | en | hi` (§14.3, §14.4). Hindi is romanised, matching `web/packages/i18n/src/hi.json`. Where a verb is gendered, both forms are given — say the one that applies to you.

### S1 — Consent to observe (0:00–0:02)

> **en** — "Namaste, and thank you for the time. I am testing an app; I am not testing you. There is no right or wrong answer here, and nothing you do can be wrong — if something is confusing, that is the app's fault, and finding that is exactly my job today. I would like to watch the screen while you use it, and write notes. May I? I will not record your face or your name. If you want to stop at any moment, just say **bas**, and we stop immediately — you do not have to give a reason. What you say stays between us; I do not report anything to anyone where you work. Is that alright?"

> **hi** — "Namaste, aapke time ke liye dhanyavaad. Main ek app test kar raha/rahi hoon — main aapko test nahi kar raha/rahi. Yahan koi sahi ya galat jawaab nahi hai, aur aap kuch galat kar hi nahi sakte. Agar kuch samajh na aaye to wo app ki galti hai, aur wahi dhoondhna aaj mera kaam hai. Main screen dekhna chahta/chahti hoon aur notes likhna chahta/chahti hoon. Ijaazat hai? Main aapka chehra ya naam record nahi karunga/karungi. Kabhi bhi rokna ho to sirf **bas** kah dijiye — hum turant rok denge, wajah batane ki zaroorat nahi. Jo aap kahenge wo hum dono ke beech rahega; aap jahan kaam karte hain wahan main kisi ko kuch nahi bataunga/bataungi. Theek hai?"

Wait for a **spoken yes**. Tick the box on the session sheet. Hand the 14416 (Tele-MANAS) card now, not at the end — so it is never mistaken for a reaction to something they said.

### S2 — Think-aloud priming, adapted for low literacy (0:02–0:03)

Per §2, this protocol values **observation over verbalisation**: we ask what they would *do*, never why.

> **en** — "As you use it, tell me what you would tap next, and what you expect will happen. You do not have to explain why — just say what you would do. If you go quiet, I may ask 'what would you tap next?'. That is not a hint; I am only keeping up with you."

> **hi** — "Jab aap istemal karein, mujhe bataiye ki agla tap aap kahan karenge, aur kya hone ki umeed hai. Kyun — ye batane ki zaroorat nahi. Bas ye batayein ki aap kya karenge. Agar aap chup ho jaayein to main pooch sakta/sakti hoon 'ab kahan tap karenge?' — ye hint nahi hai, main sirf aapke saath chal raha/rahi hoon."

**Warm-up (not a measured task, ~20 s):** "Pehle ek aasaan cheez — apna phone unlock karke koi bhi ek app kholiye." / "First something easy — unlock your phone and open any app." Two purposes: it establishes that tapping-while-talking is normal, and it gives you the participant's **baseline tap speed**, without which the ≤ 10 s budget in T1 cannot be read honestly. Someone who takes four seconds to reach any button on their own phone is not failing our button.

### S3 — Trust question, BEFORE (0:03–0:04)

Ask once, exactly as written. Do not offer options. Do not react to the answer. Write it **verbatim**.

> **en** — "Before we start: if you used this app every day, who do you think could see your answers?"

> **hi** — "Shuru karne se pehle: agar aap ye app roz istemal karein, to aapke jawaab kaun kaun dekh sakta hai?"

If they ask what you think: "Abhi main kuch nahi bataunga/bataungi — baad mein zaroor bataunga/bataungi." / "I won't say yet — I will tell you afterwards, for certain." The identical sentence is asked again at S6; that pair is the single most important measure in this protocol (§12).

### S4 — Task framing and neutral probes

Frame every task the same way, then go silent:

> **en** — "Now one task. *\<task sentence from §11\>*. Tell me when you think you are done."
> **hi** — "Ab ek kaam. *\<§11 ka task vaakya\>*. Jab lage ki ho gaya, to bata dijiye."

Start the stopwatch the instant you stop speaking.

| Situation | Say this (en) | Say this (hi) | **Never** say |
|---|---|---|---|
| stuck and silent > 15 s | "What are you thinking?" | "Aap kya soch rahe hain?" | "Try the button at the bottom" — that hands over the answer |
| "is this right?" | "There is no right answer here. Do what you would do at home." | "Yahan sahi-galat kuch nahi hai. Jaisa aap ghar par karte, waise karein." | "Yes, that's right" / "Almost" |
| "what is this screen for?" | "What do you think it is for?" | "Aapko kya lagta hai ye kis liye hai?" | naming the screen — it contaminates §8 free recall for the rest of the session |
| taps something unexpected | "What did you expect to happen?" | "Aapko kya hone ki umeed thi?" | "That's not it" / "Go back" |
| **"is this compulsory?"** | "What would you expect?" — then log the question **verbatim**; it is itself a finding (§13 B.1) | "Aapko kya lagta hai?" | "No, it is voluntary" — that answers the very thing being measured |
| blames themselves | "You are not the problem. If it is confusing, the app is wrong — that is what I am writing down." | "Galti aapki nahi hai. Agar samajh nahi aa raha to app galat hai — main wahi likh raha/rahi hoon." | "It's easy, look…" |
| "who do you report to?" | Answer fully and honestly: a student project; no report goes to their workplace; no names are written anywhere. | "Ye ek student project hai. Aap jahan kaam karte hain wahan koi report nahi jaati, aur kisi ka naam kahin nahi likha jaata." | anything vague — evasion here poisons every trust measure in the session |
| after a failed task | "That helps a lot. Let's go on." | "Isse bahut madad mili. Aage chalte hain." | "You'll get it next time" — it tells them they failed |

**Assist ladder** — record the level *before* you give it:

| 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| none | neutral probe only ("what would you tap next?") | verbal hint naming a *region* ("look near the bottom") | verbal hint naming the *control* | you point at the screen | you take the phone |

Assist **0–1 = success** · **2–4 = assisted success** · **5 = fail**. A task also fails at 2× its time budget, whichever comes first.

### S5 — SEQ, after every task (including failed ones)

Hand the printed card and read:

> **en** — "Overall, how easy or hard was that task? 1 is very hard, 7 is very easy."
> **hi** — "Kul milakar, ye kaam kitna aasaan ya mushkil laga? 1 matlab bahut mushkil, 7 matlab bahut aasaan."

The card carries 7 boxes, the numerals, a face at each end, and the two anchor words in the session language. Let them point; do not read the numbers out one by one. **Never skip the SEQ after a failure** — that is the score that matters most. This is the standard single-item post-task ease measure (SEQ; Sauro & Dumas, CHI 2009). Do not reword it and do not change the scale: comparability across sessions is the only reason to use a published item rather than one of our own.

### S6 — Trust question, AFTER (identical wording)

Ask **the same sentence as S3, word for word**. Write it verbatim. Only after it is on paper do you debrief ("Ab main aapko bata deta/deti hoon…").

### S7 — ADR-0004 perception battery

Run §8 as written. In the compressed session, items 1 and 2 only.

### S8 — Close

> **en** — "That is everything. Two last things. First: if you want, say so now and I will throw away everything I wrote in the last half hour — no questions. Second: keep this number, 14416, Tele-MANAS. It is a free national helpline, and it has nothing to do with this project or with where you work."

> **hi** — "Bas itna hi. Do aakhri baatein. Ek: agar aap kahein to main pichle aadhe ghante ka likha hua sab abhi phenk dunga/dungi — koi sawaal nahi. Do: ye number rakh lijiye, 14416, Tele-MANAS. Ye muft rashtriya helpline hai, aur is project ya aapke kaam ki jagah se iska koi lena-dena nahi hai."

**Distress stop rule (applies at every moment of the session, overriding everything above).** If the participant becomes upset: stop the task, do not probe, do not move to the next task, offer to end, hand the 14416 card, and write nothing clinical in the log — only "session ended early at participant's comfort". Tell neel and kv the same day. Log it as **S1 only if a screen or a string caused it**; life is not a finding. This is a mental-health-adjacent product being tested by students: there is no version of this protocol where we push through.

## 11. The six measured tasks (runnable core)

Order is deliberate. **T1 is first** because the core loop must be measured cold, before the participant has learned anything about the app. **T4 sits after the offline task and before withdrawal** so the participant has actually produced data by the time they go looking for who saw it — asking "who viewed your data" before there is any data teaches the wrong lesson and softens the moment.

| # | Task sentence, spoken verbatim (en / hi) | Start → end event | Budget | Success (unassisted) | Fails if | Stimulus today |
|---|---|---|---|---|---|---|
| **T1** | "Tell the app how today felt for you." / "App ko bataiye ki aaj aapko kaisa laga." *(deliberately avoids the words check-in, start, button, mood)* | starts when you stop speaking, app on `/roster`, not yet checked in → ends when the entry is stored (sheet closes; `sync.pill.queued` increments) | **≤ 3 taps, ≤ 10 s** ([design.md §10](../architecture/design/design.md), [F02 §2](../features/F02-jawan-app.md), FR-04) | stored within budget at assist 0–1, **and** on "Kya hua? Ye kahan gaya?" the participant says it was saved/sent — a check-in the user does not believe was recorded is not a completed check-in | > 6 taps, or > 20 s, or assist ≥ 2, or cannot say what happened to the answer | **built** — `web/apps/jawan/app/(tabs)/roster/` |
| **T2** | "Find out when your next duty is, and how many days of leave you have left." / "Pata kijiye ki aapki agli duty kab hai, aur kitni chhutti baaki hai." | starts as above → ends when both facts are read aloud | **0 navigational taps, ≤ 30 s** — both facts sit on the home screen (`roster.nextDuty`, `roster.leaveBalance`; `roster/page.tsx:17–18`) | both read correctly without leaving the home screen | hunts through the tabs, or reads the wrong card | **built** |
| **T3** | *(you turn airplane mode on, visibly)* "There is no network now. Do the check-in again — imagine it is tomorrow." / "Abhi network nahi hai. Check-in dobara kijiye — maan lijiye kal ka din hai." Then: "Aapka jawaab kahan gaya? Wo chala gaya ya yahin hai?" | starts as above → ends after the participant answers the where-did-it-go question | **≤ 3 taps, ≤ 45 s** including the question | completes with no visible error **and** the participant says the data is saved and will be sent — that is the whole job of `sync.pill.queued` ([ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md): the user need not understand sync, but must not fear loss) | any data loss (**S1**, §7); any alarm/red styling on queued data; or the participant believes the answer was lost | **built** — *must run against a production build*, see the setup note below |
| **T4** | **the trust moment** — "Find out whether anyone has looked at what you entered, and who." / "Pata lagaiye ki aapne jo bhara hai use kisi ne dekha hai ya nahi — aur kisne." *(never says "who viewed my data", "receipts" or "Me": the label is the thing under test)* | starts as above → ends when the participant answers **who / when / why** from what is on screen | **≤ 3 taps, ≤ 60 s** | reaches the receipt list unassisted **and** answers all three — who (role), when, and **why** (the purpose string). A receipt that is found but not understood is decoration ([design.md §5](../architecture/design/design.md)) | not found in 60 s; or found but cannot say why the person looked; or read as an accusation ("mujhe kuch hua hai kya?") — that last one fails the "receipt, not warning" intent and is **≥ S2** | **prototype** — `/me/receipts` renders `coming.soon` (`me/page.tsx:27`); run on the UX-002 mockup, Confidence = `prototype` |
| **T5** | "You have decided you no longer want to share the daily check-in. Stop it." / "Aapne tay kiya ki ab roz ka check-in share nahi karna. Use band kar dijiye." | starts as above → ends when the scope is withdrawn and confirmed | **≤ 4 taps, ≤ 90 s** | withdraws it, **and** afterwards can say what happens to data already given and whether anyone gets told — FR-17 silent withdrawal is only real if the user understands that it is silent | cannot find it; or withdrawal is **deeper than granting** (design.md §10, F02 §5 — measure both depths in the same session: granting was 1 tap inside the sheet, `CheckInSheet.tsx:175`); or withdraws but believes it will "look bad" — log that verbatim as a §13 coercion signal, **not** a task failure | **prototype** — `/me/consent` renders `coming.soon` |
| **T6** | "This month there are some questions. Start them, and answer the first one — without using the keyboard." / "Is mahine kuch sawaal hain. Unhe shuru kijiye aur pehla sawaal ka jawaab dijiye — keyboard istemal kiye bina." | starts as above → ends when the first item is answered | **≤ 120 s** | first item answered with the keyboard never opening; the disclaimer is noticed (ask "Ye upar kya likha hai?"; accept any paraphrase of `screen.disclaimer`); and the participant can restate the voice privacy line's meaning (§14.3 layer 1) | the keyboard opens; the flow cannot be started; the disclaimer is not noticed at all | **prototype** — no instrument flow and **no mic exist** (§14.4 #5). Run §14.3 layers 2–4 here |

**T3 setup, non-negotiable.** Run against a **production** build. The service worker registers in production only and dev actively unregisters it (`apps/jawan/app/sw-register.tsx`), so an offline test on `next dev` tests nothing. In `web/apps/jawan`: `bun run build` then `bun run start`, load `/roster` once **online** so the shell caches, then airplane mode. Of the app's routes only `/` and `/roster` are precached (`public/sw.js` `SHELL`, which also holds `/manifest.webmanifest` and `/icons/icon.svg`), with navigations network-first falling back to the cached shell — so keep T3 on the roster tab.

**T1 tap count, counted from the code (not estimated).** Steady state: `home.checkin.open` (1) → emoji (2) → `checkin.submit` (3) = **3 taps**; the slider defaults to 5 and never needs touching. The **first-ever** check-in is **4 taps** — the consent checkbox is required on the first save only (`CheckInSheet.tsx:33, 69–81, 175`). A first-run participant is therefore *structurally one tap over budget*. Record first-run and repeat runs separately and never average them; if the 4-tap first run is judged acceptable, that decision belongs in F02 §2, not in a spreadsheet.

**T2 note.** The service cards are non-interactive `<article>` elements (`roster/page.tsx:40`) with no detail screen. "Tried to tap the card and nothing happened" is **not** a participant failure — it is an affordance-without-action finding (S3) against APP-002. T2 is also the **ADR-0004 test in task form**: if the roster facts are harder to reach than the check-in, the app is a wellness app wearing a roster costume.

**T4 follow-up, asked once.** "Agar yahan kisi ka naam hota jise aap nahi jaante, to aap kya karte?" / "If a name you did not recognise were listed here, what would you do?" No action path exists in v1; the answer tells us whether one is needed (feeds the F08/F02 backlog). The role labels the participant must read back come from `whoViewed.role.*`; the purpose string is the audit-log reason (design.md §5).

**T5 — the string that carries the criterion.** `consent.withdraw.silent` ("Withdrawing is silent. Command will not see it, and it is never held against you." / "Wapas lena chup-chaap hota hai. Command ko pata nahi chalta, aur iska koi nuksaan nahi.") is the sentence under test, alongside `consent.withdraw.confirm` and `consent.withdrawn`. Success requires the participant to *restate* it, not to have read past it. If they withdraw and still believe someone will be told, the string has failed — an **S2** against APP-004, and a §13 B.6 tick if the reason they give is social.

**T6 — safety boundary, non-negotiable.** The instrument bank includes **PHQ-9 item 9 (self-harm)**, and the app now carries the strings for its escalation path (`instrument.safety.title` / `.body` / `.call` / `.counsellor`). In a usability session the participant answers **the first item only**, which is why T6 is written that way. Never administer a full instrument, never reach item 9, and never treat an instrument answer as data — we are testing whether a screen can be operated, not screening a human being. If a participant volunteers distressing content anyway, the §10 S8 stop rule applies immediately. The `instrument.safety.*` flow is reviewed separately as a **content** review with a counsellor present, not inside a usability session run by a student.

## 12. Measures — definitions precise enough that two moderators score alike

| Measure | Definition | Instrument |
|---|---|---|
| **Task success** | three levels: **success** (assist 0–1) · **assisted success** (assist 2–4) · **fail** (assist 5, or > 2× time budget, or the task's stated fail condition) | observer + §11 fail conditions |
| **Time on task** | starts the instant the moderator stops speaking the task sentence; stops at the task's stated **end event**, not at "seems done". Probes do **not** pause the clock; a moderator interruption does — note the pause | one stopwatch, one person |
| **Taps** | a discrete deliberate touch intended to change state. A slider drag = 1. A scroll = 0. A tap on a dead area = 0 taps and 1 error. Counted from the recording, never live | screen recording — **screen only**, no face, no audio containing a name |
| **Errors** | any action that moves off the success path, including taps on non-interactive elements | observer + recording |
| **Recovery** | returning to the path at assist 0–1. Record as a pair, e.g. `3/2` — three errors, two recovered, one not | observer |
| **SEQ** | the 7-point single-item ease question, asked verbatim (§10 S5) after **every** task, failures included | printed card |

**The trust question — asked identically before and after (§10 S3 / S6).** Written verbatim, then coded afterwards against a fixed list; the moderator never paraphrases into a category during the session.

`nobody` · `only me` · `the app / the company` · `counsellor / doctor` · `welfare officer / sahab` · `my CO / commandant` · `HQ / department` · `anyone who wants to` · `don't know`

Report it as **movement**, not as a score: `before → after` per participant, plus how many moved *toward* the architecture's actual answer (counsellor only, after dual-key, and receipted) and how many moved *away*. A product that leaves the belief unchanged has failed to communicate the firewall. A product that moves the belief **away** has actively misled, and that is **S1** (§9.1 b).

**Recorded per session, always:** device class (§5) · build sha and mode (`dev` / **production** — offline results from a dev build are void) · session language · whether the participant reads romanised Hindi · §13 checklist · §8 battery.

**Targets — reasoned, not evidence** (same status as §7; AGENTS.md rule 7):

| Measure | Target | Confidence |
|---|---|---|
| T1 unassisted success | ≥ 8 / 10 | **Med** — direct 3-tap code path |
| T1 time, repeat run, floor device | ≤ 10 s median, ≤ 15 s p90 | **Med** |
| T4 unassisted success | ≥ 7 / 10 | **Low** — prototype stimulus |
| SEQ per task | median ≥ 5 / 7 | **Low** — no baseline exists for this population |
| Trust-question movement | ≥ 6 / 10 move toward the real answer; **0** move away | **Low** — and it is the number we would most like to be wrong about |
| Icon comprehension | per §4 (≥ 4 of 5) | **Low** |

None of these numbers is evidence of anything. They are the thresholds at which we stop and change the design — nothing more.

## 13. Signals of coercion — checklist

[F02](../features/F02-jawan-app.md) states it plainly: **a coerced check-in is a falsified data point**, and [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) names individual incentives and streaks as anti-patterns. Coercion does not present as a task failure — it presents as a fast, cheerful, false answer that scores as a *success*. So it needs its own instrument, run every session, including clean ones.

### A — Build audit (10 minutes, once per tested build, by whoever prepares the session)

- [ ] no streak counter, badge, day-count or participation percentage on any screen
- [ ] no notification that repeats, escalates, or references a missed day (v1 ships none — confirm none was added)
- [ ] no individual reward, priority or leave-preference language in either dictionary — `grep -rniE "reward|inaam|streak|priority|leaderboard" web/packages/i18n/src/`
- [ ] no leaderboard and no peer or unit comparison visible to a jawan
- [ ] roster, leave and pay-slip facts remain reachable with every welfare consent withdrawn — **re-run T2 immediately after T5**; non-participation must cost nothing
- [ ] withdrawal depth ≤ granting depth (measured in T5)
- [ ] the check-in card carries no counter and no "pending" state (`CheckInCard.tsx`)

### B — Session observation (tick as it happens; record, do not interpret)

1. [ ] participant asks whether the check-in is compulsory ("sir, ye zaroori hai kya?") — **log the verbatim**
2. [ ] participant looks at the moderator, or at anyone else in the room, before choosing the mood
3. [ ] participant selects the neutral or positive emoji in under 2 s without reading the labels — the *"sab theek hai, bas thaka hua hoon"* answer that [personas §1](../product/personas.md) names as the default and F04 exists to survive
4. [ ] participant changes an answer after being told a counsellor might see it
5. [ ] participant asks whether the answer reaches "sahab" / "CO sahab" / the office
6. [ ] participant declines to withdraw a consent in T5 for a **social** reason ("achha nahi lagega", "sochenge kuch hai")
7. [ ] participant asks whether *not* doing it would be noticed
8. [ ] a senior, supervisor, employer or family elder is present in the room or within earshot

### C — Scoring rules

- **Any tick on B.8 voids the session's welfare data.** Reschedule, alone. Nothing else in this protocol can be read from a session with an observer present, because the entire construct is whether people answer honestly when they might be watched.
- **Two or more B ticks** → that session's check-in *values* (mood, slider) are marked `coerced?` and excluded from any distribution. The ticks themselves remain findings.
- Any B tick at all → a row in §15, at **S1 if it points at a product feature** (a nag, a count, a reward, a phrase) and **S3 if it points only at the environment** — which we cannot fix in software, but must state in the pilot design.
- B.1 and B.5 are also **content** findings: the app is not saying clearly enough who sees this and that it is voluntary. Copy is a candidate fix, and copy is testable — write the proposed key into §15 and retest it.

## 14. Icon + voice review

Reviewed against the code as of 2026-09-09: `web/packages/ui/src/Icons.tsx`, `CareStateChip.tsx`, `ui.css`, `web/packages/tokens/src/tokens.json`, and every render site in `web/apps/jawan/app/`. This is a review of what exists, not of what the docs describe.

**Re-verification rule.** `packages/ui` and the two dictionaries are moving under active parallel work, so every claim here is a claim about a **build**, not about the product. Before session 1, re-run the four checks this section rests on and correct any row that has moved: (1) `grep -rn "Icon" web/apps/jawan/app/` — the render sites in §14.1; (2) `grep -rnE "getUserMedia|MediaRecorder|AudioContext" web/apps web/packages` — §14.3 must still return zero; (3) `grep -rn "setLocale\|LanguageToggle" web/apps/jawan/` — §14.4 #6; (4) the fallback hexes in `packages/tokens/src/tokens.json` against §14.2's table. A stale defect list is worse than none: it sends a participant into a build nobody checked.

### 14.1 Icon-by-icon

**Scope of the table.** `Icons.tsx` now exports 32 glyphs; the table below covers the **ten the jawan app actually renders**. The rest (`IconMic`, `IconChart`, `IconLock`, … ) are exported but unrendered on any jawan screen and are reviewed when a screen picks them up.

**Two findings frame the whole table.** First, every icon is `aria-hidden="true"` by construction (`Icons.tsx:12`, inside `base()`), and **every icon the jawan app renders is paired with a visible localised text label** — there is no icon-only control on any jawan screen. The shared package does now ship three icon-only close buttons (`BaseDialog.tsx:63`, `Toast.tsx:32`, `UndoBar.tsx:35` — an `IconX` under `aria-label={t("a11y.close")}`); those satisfy design.md §9's actual clause (unambiguous glyph **plus** an accessible name) and none is rendered on a jawan screen today, so no §11 task touches one. Re-check this paragraph the moment a jawan screen imports a dialog, toast or undo bar. Second, the real problem is therefore not accessibility but **overloading**: `IconHeart` and `IconUser` each carry four different meanings, and `IconClipboard` three. For a user navigating by shape rather than by text, a glyph with four meanings carries none.

| Icon (`Icons.tsx`) | Meant to say | Rendered where today | Visible text label there? | Misread risk in a low-literacy uniformed context | Verdict |
|---|---|---|---|---|---|
| `IconClipboard` (L16) | a duty list | Roster tab (`layout.tsx:13` → `nav.roster`) · Duty-roster card (`roster/page.tsx:17`) · **Grievance card** (`roster/page.tsx:21`) | **yes** at all three (`sa-tab__label`; `service-card__label`, `roster/page.tsx:44`) | **M** — one glyph, three meanings, two of them on the same screen: the Roster tab and the Grievance card are shape-identical. A clipboard is also a clerk's object; in unit lines the roster is a *board*, not a clipboard | **keep** for Roster (tab and card sharing it is correct — it teaches the tab); **redraw** a distinct glyph for Grievance |
| `IconHeart` (L24) | welfare, care | Welfare tab (`layout.tsx:14`) · Canteen card (`roster/page.tsx:20`) · Family-welfare card (`roster/page.tsx:22`) · Unit-pulse row (`welfare/page.tsx:8`) | **yes** at all four | **H** — a heart on a mental-health-adjacent app is the single most on-the-nose "therapy app" signal, which is exactly what ADR-0004 buys us out of; it also currently means *canteen*; and from social apps it reads as "like / romance" | **redraw** — Welfare gets a non-clinical glyph (two figures / a hand and a figure); canteen gets a plate or cup; family welfare gets a family group. If §8 free recall returns "health app", check the heart first |
| `IconUser` (L30) | a person, me | Me tab (`layout.tsx:15`) · **Leave-application card** (`roster/page.tsx:18`) · Battle-buddy row (`welfare/page.tsx:9`) · **Who-viewed-my-data row** (`me/page.tsx:8`) | **yes** at all four | **H** — four meanings, one of which (leave application) has nothing to do with a person; and the trust moment (`me.receipts`) is marked with a *person* glyph, which reads as "your profile", not "someone looked at you". Battle buddy needs two figures, not one | **keep** for `nav.me`; **redraw** leave (calendar with a tick), buddy (two figures), receipts (a list with an eye) — receipts first, per design.md §5's "receipt, not warning" |
| `IconLeaf` (L37) | care state `green`, "Sab theek" | `CareStateChip.tsx:31` **only** — and `CareStateChip` is imported by no screen (only `packages/ui/src/index.ts`) | **yes** — `care.chip.green` at `CareStateChip.tsx:32` | **H** standalone — a leaf reads as "patta / paudha / eco product". Nothing in it says "all good". It works only as the bottom rung of a ladder *seen together*, and the app shows one chip at a time, never the ladder | **pair with label (mandatory, already true) + retest.** Never ship it icon-only. Redraw if §4's ≥ 4/5 threshold misses |
| `IconSun` (L44) | care state `amber`, "Thoda dhyan do" | `CareStateChip.tsx:31` only | **yes** — `care.chip.amber` | **H** — a sun reads as "din / dhoop / mausam / subah"; there is no semantic path to "pay a little attention". Worse, it is drawn as 8 rays at `strokeWidth 1.8` and rendered at **16×16** (`CareStateChip.tsx:31`): on the §5 floor device the rays fall below one device pixel and the glyph collapses into a plain circle — at which point it is indistinguishable from `IconClock` and `IconGlobe`, which are also circle-first | **redraw** at a single 16 px optical size (≤ 2 path elements), or render the chip icon at 20–24 px |
| `IconHandHeart` (L51) | care state `red`, "Baat karo" | `CareStateChip.tsx:31` only | **yes** — `care.chip.red` | **M/H** — three `<path>` elements with three stacked finger arcs plus a heart: the most complex glyph in the set, at 16 px. On the floor device it is a blob. Semantically it is the strongest of the four *if legible* — an offered hand reads as help | **redraw for 16 px** — hand plus heart, drop the finger arcs. Keep the concept |
| `IconPhone` (L59) | care state `critical`, "Turant" | `CareStateChip.tsx:31` only | **yes** — `care.chip.critical` | **L** — a handset is among the most universally recognised glyphs, and here the action genuinely is a call (14416, F02 §7). Minor caveat: a landline silhouette is dated, but it remains the call glyph on every Android dialer | **keep** |
| `IconShield` (L65) | consent | Consent row (`me/page.tsx:7` → `me.consent` "Sahmati") | **yes** | **H in this context** — in a uniformed force a shield reads as insignia, security branch, "the organisation protects you": the exact inverse of "this is your permission, and you can take it back". Consent is about the user's control, not the institution's protection | **redraw** — a key, or a thumb impression. A thumb impression is the most literacy-independent consent glyph in an Indian government context and is what giving permission actually looks like to this user. Test that variant in §4 |
| `IconGlobe` (L71) | settings | Settings row (`me/page.tsx:9` → `me.settings`) | **yes** | **H** — a globe means "internet / online / language" in every app this user has. In an **offline-first** product a globe beside Settings teaches the wrong mental model ("this needs internet"), and the language switch it evokes does not exist (§14.4 #6) | **redraw** — a gear for Settings; reserve a globe or "अ\|A" for the language row once there is one |
| `IconClock` (L78) | time | Pay-slip card (`roster/page.tsx:19`) · My-trend row (`welfare/page.tsx:7`) | **yes** at both | **M** — a clock for a **pay slip** is arbitrary; a pay slip is money and a document. For a 90-day trend it is defensible, but a rising line is better | **redraw** pay slip (rupee or document); **pair with label + retest** for trend, with a line-chart glyph preferred |
| **Emoji row** (`CheckInSheet.tsx:10`, rendered 120–136) | today's mood, 5 steps | Check-in sheet | **yes** — `checkin.emoji.1–5` at `CheckInSheet.tsx:135` | **H**, for two independent reasons. **(a) Semantic mismatch:** the glyphs encode *valence* (😞→😄, sad→happy) while the labels encode *load* ("Bahut bhaari"→"Bahut halka", heavy→light). A reader resolves this from the label; a non-reader resolves it from the face and answers a different question — two participants give the "same" answer meaning different things. **(b) System emoji:** the font is the OEM's, so on the API 26 floor device the five faces may not render as a monotonic series at all. Neither risk is visible on a laptop | **redraw as drawn faces in `Icons.tsx`** if the floor-device check fails, and **pick one axis** — draw faces for load, or switch the labels to valence. Against **APP-003** |
| **Slider** (`CheckInSheet.tsx:152`) | not an icon — the other half of the same measurement | Check-in sheet | label only (`checkin.slider.label`), plus a live number that is `aria-hidden="true"` (`CheckInSheet.tsx:159`) | **H** — the track has **no end anchors**. A user who cannot read the label has nothing telling them which end is heavy; a user who can read it still gets no anchor at the ends | **pair with labels** — add `checkin.slider.min` / `.max` at the track ends (proposed keys — neither exists yet; route the wording to the i18n owner as in §14.3), and give the input an `aria-valuetext` or drop `aria-hidden` from the value |

### 14.2 The care-state ladder — colour is not carrying it, and must not

**Confirmed: none of the four rungs is distinguished by colour alone.** `CareStateChip.tsx:30–33` renders `<Icon>` **and** `t(LABEL_KEYS[state])` inside every chip, and there is no code path that produces a chip without both. That is verified in code, not inferred from intent.

**Also confirmed, and it changes how §4 must be run:** the ladder is currently rendered on **no screen** — `CareStateChip` is imported only by `packages/ui/src/index.ts`. So §4's icon-comprehension check runs against a printed or prototype stimulus card this round, and every ladder finding carries Confidence = `prototype`.

| Rung | Token | OKLCH (`tokens.json`) | ΔL to its neighbour | Hue axis | What survives deuteranopia / protanopia |
|---|---|---|---|---|---|
| `green` "Sab theek" | `state/green` | L **0.62** C 0.13 H 150 | — | green (150) | lightness 0.62 only |
| `amber` "Thoda dhyan do" | `state/amber` | L **0.75** C 0.14 H 80 | +0.13 vs green | yellow (80) | lightness **and** hue — 80° sits near the blue–yellow axis a red–green dichromat keeps |
| `red` "Baat karo" | `state/red` | L **0.55** C 0.17 H 25 | −0.07 vs green | red (25) | lightness 0.55 only |
| `critical` "Turant" | `state/critical` | L **0.45** C 0.15 H 25 | −0.10 vs red | red (25) | lightness 0.45 only |

The reasoning, in lightness terms:

1. Dichromacy removes a chromatic axis but leaves the **luminance** channel intact. OKLCH `L` is the perceptual lightness axis, so **ΔL is what actually survives** — which is why this ladder has to be argued in `L`, not in hex.
2. The pair that collapses in hue is **green (H 150) against red (H 25)** — precisely the red–green axis deuteranopia and protanopia remove. Their ΔL is **0.07, the smallest gap in the ladder.** So the weakest pair for a dichromat is *green vs red*: the two rungs whose meanings are furthest apart ("all good" and "let's talk").
3. **Amber is the safest rung** — H 80 is on the axis a red–green dichromat retains, and it is ΔL 0.13 from its nearest neighbour.
4. **Red and critical are a lightness pair for everyone.** Same hue (25), similar chroma, ΔL 0.10; no viewer, dichromat or not, separates them by hue name — both are "red". That is acceptable *because* the icons differ (hand-heart vs phone) and the labels differ, but it means colour contributes nothing to that step.
5. **Net:** for a red–green dichromat the colour channel carries at most **one** reliable distinction (amber vs the rest). The icon and the label do the real work — which is what design.md §2 claims and what the code honours. On this ladder colour is decoration; treat any future change that makes colour load-bearing as a regression.

**Proposal P1** (record as a finding; do **not** apply mid-protocol, or the tested build stops matching the shipped one): raise the green↔red separation to **ΔL ≥ 0.12** — either `state/green` → `oklch(0.68 0.12 150)` or `state/red` → `oklch(0.50 0.17 25)`. Land it with UX-002 and design.md §2 together.

**Measured contrast — and why the hex fallbacks are the numbers that matter.** `packages/tokens/dist/tokens.css` declares each colour **twice**, hex first and `oklch()` second, so a browser without `oklch()` support paints the hex. The API 26 / Android 8 WebView on the §5 floor device supports neither `oklch()` nor `color-mix()` — **the fallback hexes in `tokens.json` are literally what the reference test device paints.** Ratios below are WCAG 2.x relative luminance against `surface/base` `#f7f6f2`.

| Element (code) | Colour pair | Ratio | Floor (design.md §9 / §6) | Verdict |
|---|---|---|---|---|
| `.sa-chip--green` label text (`ui.css:50`) | `#4a8a55` on `#f7f6f2` | **3.84 : 1** | 4.5 : 1 | **fail** |
| `.sa-chip--amber` label text (`ui.css:51`) | `#e0a020` on `#f7f6f2` | **2.11 : 1** | 4.5 : 1 | **fail** |
| `.sa-chip--red` label text (`ui.css:52`) | `#c04535` on `#f7f6f2` | 4.69 : 1 | 4.5 : 1 | pass |
| `.sa-chip--critical` label text (`ui.css:53`) | `#8f2f25` on `#f7f6f2` | 7.47 : 1 | 4.5 : 1 | pass |
| `.sa-checkincard__cta` — the one saffron CTA (`ui.css:91–94`) | `#ffffff` on `#d98a1e` | **2.76 : 1** | 4.5 : 1 | **fail** |
| focus ring (`ui.css:18–19`, `122–123`) | `#d98a1e` on `#f7f6f2` | **2.55 : 1** | 3 : 1 non-text (design.md §6) | **fail** |
| `.sa-syncpill--error` (`ui.css:67`), `.login-error`, `.sheet__error` | `#e0a020` on `#f7f6f2` | **2.11 : 1** | 4.5 : 1 | **fail** |
| `.sa-btn--primary` (`ui.css:26–29`) | `#ffffff` on `#5a6b33` | 5.86 : 1 | 4.5 : 1 | pass |

Honest caveat: the chip *background* is a 12–15 % tint of the same colour and so is marginally darker than `surface/base` — the real chip ratios are slightly **lower** than shown, never higher. Method is reproducible from the two hexes in any contrast checker; the figures came from a 12-line WCAG relative-luminance script over the `fallback` values in `tokens.json`.

These are simultaneously an accessibility-floor breach **and** a confound for this protocol: a §4 comprehension miss on the amber chip cannot be blamed on the icon while the label beside it sits at 2.1 : 1. Fix before session 1 (§14.4). The replacement values are a design decision for review — this document records measurements; it does not retint the product mid-protocol.

### 14.3 Voice review

**Current state, verified.** `grep -rnE "getUserMedia|MediaRecorder|AudioContext" web/apps web/packages` returns **zero** hits: there is no capture path in the codebase at all. `IconMic` and `IconMicOff` glyphs now exist (`Icons.tsx:100,108`) and are exported, but no component and no screen renders either. (A bare `grep -i mic` is *not* the check — it also matches the word "Microphone" inside `voice.denied` in both dictionaries, which is a string, not an affordance.) The F03 voice affordance does not exist yet:

| F03 / design.md §6 requirement | In the code today |
|---|---|
| every text input carries a mic affordance | **none.** The three text inputs are `checkin-note` (`CheckInSheet.tsx:168`) and `username` / `password` (`login/page.tsx`) |
| live waveform replaces the keyboard; live transcription; keep / re-record | not built |
| the honest indicator `voice.privacy.line` | **the string exists; the affordance does not.** `voice.privacy.line` and eleven sibling `voice.*` keys landed in both dictionaries on 2026-09-09 — and no component reads any of them |
| recorded voice prompts for instruments (F02 DoD) | none. The item bank now exists as a package (`web/packages/instruments/src/` — `bank.ts`, `types.ts`, `scoring.ts`, `index.ts`), but **no screen renders it** and no audio asset ships — same pattern as the strings: logic ahead of surface |

The copy has run ahead of the component, which is the good order to do it in — but it means **a string being present in `en.json` is not evidence that a user can ever see it.** Verify every claim in this section against a render site, never against the dictionary. So §14.3 is a **specification to test against a prototype**, and its findings carry Confidence = `prototype` until APP-006 lands.

**Which inputs must carry a mic — and which must never.**

| Input | Mic? | Why |
|---|---|---|
| check-in free text (`checkin.optional.label`) | **yes, required** | the only free-text welfare field in v1. Mixed literacy is a primary constraint (ADR-0005), so voice is an equal input path, not an accessibility bolt-on (design.md §6) |
| instrument items (PHQ-9 / GAD-7 / PSS-10 / ISI) | **no mic — a recorded prompt instead** | items are fixed-choice: the literacy barrier is *reading the question*, not answering it. F02's DoD asks for recorded voice prompts — audio **out**, taps **in**. A mic here would invite free speech into a scored instrument |
| grievance text (F01 / HRMS surface) | yes, once the real screen exists | same literacy argument; outside v1 prototype scope |
| unit-pulse rating, buddy state | no | 1–5 and 3-state pickers; nothing to dictate |
| `username` / `password` (`login/page.tsx`) | **no — never** | a password spoken aloud in unit lines is overheard by whoever is standing there. Voice on a credential field converts a literacy aid into a credential leak, and it is the one input where the bystander threat is certain rather than probable |

**Exact wording to test — the shipped keys.** These are in `en.json` / `hi.json` as of 2026-09-09 (another agent owns those files this round; do not edit them here). Test this wording, not a paraphrase of it, and quote the key in every finding.

| Key | `en` | `hi` |
|---|---|---|
| `voice.privacy.line` | Your voice never leaves this phone. | Aapki awaaz phone se bahar nahi jaati. |
| `voice.start` | Speak instead of typing | Likhne ki jagah boliye |
| `voice.stop` | Stop | Rokein |
| `voice.analysing` | Listening… | Sun raha hai… |
| `voice.keep` | Keep | Rakhein |
| `voice.rerecord` | Record again | Dobara record karein |
| `voice.discard` | Discard | Hata dein |
| `voice.saved` | Saved — only the voice pattern, never the recording. | Save hua — sirf awaaz ka pattern, recording kabhi nahi. |
| `voice.explain` | The phone measures pace and pauses on this device and sends only those numbers. | Phone isi device par raftaar aur ruknay ko naapta hai, sirf wahi numbers bhejta hai. |
| `voice.unsupported` | This phone's browser cannot record. You can type instead. | Is phone ka browser record nahi kar sakta. Aap likh sakte hain. |
| `voice.denied` | Microphone permission was refused. You can type instead. | Microphone ki permission nahi mili. Aap likh sakte hain. |
| `voice.tooShort` | Speak for at least 5 seconds. | Kam se kam 5 second boliye. |

**Two keys this review proposes to add** — everything else it wanted is already covered by `voice.explain` and `voice.saved` above. If accepted, they belong in [F03](../features/F03-on-device-signals.md) §1 in the same PR that lands them (AGENTS.md rule 1), and the wording goes to the i18n owner, not into these files from here:

| Key | `en` | `hi` | Why it is needed |
|---|---|---|---|
| `voice.bystander.note` | Someone nearby can hear you. You can type instead. | Aas-paas koi sun sakta hai. Aap likh bhi sakte hain. | Every shipped string addresses the **network** ("never leaves this phone"). None addresses the **room**, which layer 3 below exists to detect and which is the likelier barrier in unit lines |
| `voice.proof.open` | See what was sent | Dekhein kya bheja gaya | `voice.explain` *states* what was sent; layer 4 tests whether the user can **check** it. This is the link from the claim to the receipt |

Two wording risks to watch in the shipped set, both testable at layer 1: `voice.analysing` renders as "Sun raha hai…" — grammatically the *phone* is listening, which is exactly the impression `voice.privacy.line` is trying to remove ("Sun rahe hain…"/"we are listening" is worse, not better — consider a non-agentive form). And `voice.discard` = "Hata dein" reads as *remove it from the list*, not *destroy it*; if layer 4 hinges on the user believing deletion is real, that verb is carrying weight it may not bear.

**How to test that users BELIEVE the claim, not merely read it.** Four layers, run in order, scored per participant. Asking "do you trust it?" is worthless — it collects politeness. Every layer below asks for a *prediction* or a *choice* instead.

| Layer | What the moderator does | What it measures | Pass |
|---|---|---|---|
| **1 — read-back** | Point at `voice.privacy.line`. "Ye line kya keh rahi hai? Apne shabdon mein." / "What is this line saying, in your own words?" | comprehension — a claim that is not parsed cannot be believed | the paraphrase contains "phone se bahar nahi jaati" / "doesn't leave the phone" |
| **2 — consequence** | "Maan lijiye aap yahan apne sahab ke baare mein kuch bolte hain. Unhe pata chalega?" / "Suppose you said something here about your officer. Would he find out?" | belief, measured as a **prediction** rather than as an opinion | answer is "nahi" / "no", **and** the reason names the phone or the counsellor rather than politeness |
| **3 — costly choice, run twice** | Offer "type it or speak it?" for a real free-text entry: once with a second person visibly seated within earshot, once alone. Record both choices | whether the belief is about the **phone** or about the **room** | the choice does not change between the two runs |
| **4 — falsifiability** | "Agar app jhooth bol raha ho, to aapko kaise pata chalega?" / "If the app were lying, how would you find out?" | whether the claim is checkable or taken on faith. [ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)'s entire value is that it is *structurally* checkable — a user with no way to check has been given a promise, not an architecture | the answer names something they could actually do (airplane mode, the receipts screen, "koi dikha de") |

Code the result as **verified** (passes 4) · **believed on faith** (passes 1–2, fails 4) · **room-limited** (fails 3 only) · **disbelieved** · **not understood** (fails 1). Only *verified* counts as a pass for §7. A **room-limited** result is a finding about the **product**, not the participant: our claim covers the network and says nothing about the bystander — which is what `voice.bystander.note` exists to fix.

If layer 4 fails for ≥ 2 participants, the fix is to make the claim **checkable in-product**, not to reword it:
- during onboarding, run a voice capture with the phone in airplane mode and show the outbox contents — F03 already guarantees the payload is the feature vector only, so show it;
- surface the signal-ingestion row in the who-viewed receipt timeline (already required by F03's DoD) carrying the proposed `voice.proof.open` (below — not yet in either dictionary);
- keep a visible `voice.discard` on the captured note until it is queued.

That is the difference between a privacy *claim* and a privacy *receipt* — and the receipt is what design.md §5 says this product actually sells.

**Romanisation caveat.** `hi.json` ships romanised Hindi in Latin script, and `<html lang="en">` is hardcoded (`apps/jawan/app/layout.tsx`) while the locale rides on `data-locale` (`packages/i18n/src/index.tsx`). For a Hindi session the romanisation is itself a variable: a Hindi-first low-literacy participant may read Devanagari and not Latin. **Ask, never assume** — it is screener question 3 (§2.3). If a participant cannot read romanised Hindi, that is an **S2 finding against the i18n strategy**, not a participant failure.

### 14.4 Fix before session 1 — defects this review found in the current build

Running a protocol against a knowingly broken build wastes participants, who are the scarcest resource here.

| # | Defect (verified in code) | Why it must be fixed first | Owner |
|---|---|---|---|
| 1 | care-chip label contrast: green 3.84 : 1, amber 2.11 : 1 (§14.2) | confounds every §4 icon-comprehension result | UX-002 + design.md §2 |
| 2 | saffron CTA `#ffffff` on `#d98a1e` = 2.76 : 1 (`ui.css:91–94`) | the Task 1 button itself is below the floor | UX-002 |
| 3 | focus ring at 2.55 : 1 against a 3 : 1 rule (`ui.css:18–19`, `122–123`) | keyboard and console tasks become unobservable | UX-002 |
| 4 | `CheckInCard.tsx:21` renders `home.checkin.empty` — "First check-in — takes 10 seconds." / "Pehli baar check-in — 10 second lagenge." — **after** a successful check-in. The correct string **already exists and is unused**: `home.checkin.doneToday` ("Checked in today. Thank you." / "Aaj check-in ho gaya. Dhanyavaad."), as are `checkin.thanks`, `checkin.undo` and `checkin.undone` | T1's end event is "the user knows it saved", and today the app tells them the opposite — that breaks the success criterion and the §12 measure at once. It is a one-key fix | **APP-003** |
| 5 | no capture path anywhere — zero `getUserMedia` / `MediaRecorder` hits — although all twelve `voice.*` strings and the `IconMic` / `IconMicOff` glyphs now ship, unrendered (§14.3) | T6 has no stimulus in the built app | APP-006 |
| 6 | no language switcher **on any jawan screen**. A `LanguageToggle` now exists in the shared package (`packages/ui/src/LanguageToggle.tsx`, the only caller of `setLocale` from `packages/i18n/src/index.tsx`) but nothing under `apps/jawan/app/` imports it — same logic-ahead-of-surface pattern as `CareStateChip` | a Hindi session still cannot be started from the UI; the moderator must set `localStorage` by hand ([Appendix A](#appendix-a--how-to-run-a-session-in-20-minutes) step 3). Downgraded from "not built" to "built, not mounted" — the fix is one import | APP-002 |
| 7 | `<html lang="en">` fixed regardless of locale (`app/layout.tsx`) | screen-reader language identification; low severity, free to fix | APP-001 |

Not defects, but scope facts that set the Confidence column: `/me/consent`, `/me/receipts` and `/welfare/trend` do not exist (`me/page.tsx:27`, `welfare/page.tsx:27` render `coming.soon`), so **T4, T5 and T6 run on the UX-002 prototype this round**.

## 15. Findings log

Three tables per session. tejas / risa fill them during and immediately after the session; neel assigns severity and owner in the review.

### 15.1 Session sheet (fill before the participant arrives)

| Field | Value |
|---|---|
| Session ID (`US-<yyyymmdd>-<nn>`) | |
| Date · start · end | |
| Moderator · note-taker | |
| Participant segment (§2.1) | |
| Confidence class | proxy / near-target / target |
| Literacy (self-reported, §2) | low / intermediate / high |
| Reads romanised Hindi? (§2.3 q3) | yes / no / partly |
| Session language | en / hi |
| Device class (§5) | floor / mid / console |
| Build sha · mode | `<sha>` · dev / **production** |
| Consent to observe, spoken (§10 S1) | yes / no |
| 14416 card handed | yes |
| Session voided (§13 C) | no / yes + reason |

### 15.2 Per-task results

| Task | Success (S / AS / F) | Time (s) | Taps | Errors / recoveries | Max assist (0–5) | SEQ (1–7) | Notes |
|---|---|---|---|---|---|---|---|
| T1 check-in | | | | | | | |
| T2 roster | | | | | | | |
| T3 offline | | | | | | | |
| T4 who viewed my data | | | | | | | |
| T5 withdraw consent | | | | | | | |
| T6 voice | | | | | | | |

Trust question (§10 S3 / S6 — the identical sentence, twice):

| | Verbatim answer | Code (§12) |
|---|---|---|
| Before | | |
| After | | |
| Movement | toward / unchanged / **away** (away = S1) | |

§13 B ticks this session: `1 ☐ 2 ☐ 3 ☐ 4 ☐ 5 ☐ 6 ☐ 7 ☐ 8 ☐` — total ____ (≥ 2 → mark values `coerced?`; any tick on 8 → session **void**)

### 15.3 Findings

| ID | Session | Segment | Task | Screen / component (file) | What happened (observed only) | Verbatim quote (lang) | Assist | Sev | Confidence | Owning task | Fix-by | Status | Retest in |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UX-001-F01 | | | | | | | | | | | | | |
| UX-001-F02 | | | | | | | | | | | | | |
| UX-001-F03 | | | | | | | | | | | | | |
| UX-001-F04 | | | | | | | | | | | | | |
| UX-001-F05 | | | | | | | | | | | | | |
| UX-001-F06 | | | | | | | | | | | | | |
| UX-001-F07 | | | | | | | | | | | | | |
| UX-001-F08 | | | | | | | | | | | | | |
| UX-001-F09 | | | | | | | | | | | | | |
| UX-001-F10 | | | | | | | | | | | | | |

**Four rules for filling it:**
1. One row per **observation**, not per opinion. If you cannot point at what the participant *did*, it is not a finding.
2. "What happened" contains no *because*. The because belongs in the review with neel.
3. Quote in the language it was spoken, romanised, verbatim. Do not translate while writing.
4. **Sev, Owning task and Fix-by may be left blank** by the note-taker — neel assigns them (§9.1, §9.2). Confidence is `proxy` unless the participant is serving personnel.

## Appendix A — how to run a session in 20 minutes

For a first-year running a session alone. The full protocol is 45 minutes (§2); this is the compressed run. Every line points back to a section — **do not improvise the wording**.

### Before the participant arrives (15 min, once per day, not per session)

1. **Build and serve production.** In `web/apps/jawan`: `bun run build`, then `bun run start` (port 3100). **Not `bun run dev`** — the service worker registers in production only (`app/sw-register.tsx`), so an offline test on a dev build tests nothing.
2. **Warm the cache.** On the test phone (same Wi-Fi, use the laptop's LAN IP, not `localhost`), open the app, sign in as `jawan.demo`, and load `/roster` once **online** so the shell caches.
3. **Set the language.** No switcher is mounted on any jawan screen yet (§14.4 #6 — the `LanguageToggle` component exists but nothing imports it; if that changes, use it and skip this step). For a Hindi session, in the phone browser console (or over remote debugging): `localStorage.setItem("saarthi.locale","hi")`, then reload. Confirm the home title reads "Aaj kaisa laga? (10 second)" **before** the participant sits down.
4. **Reset between participants:** clear site data for the origin — that clears the outbox, the locale and `saarthi.consented.checkin` — then redo step 3.
5. **Start the screen recorder. Screen only.** No face, no name, no audio containing a name.
6. **On the table:** printed SEQ card, session sheet (§15.1), pen, the 14416 card, a stopwatch.

### The 20 minutes

| Clock | What | Section |
|---|---|---|
| 0:00–0:02 | consent script; wait for a spoken yes; tick the box; hand the 14416 card | §10 S1 |
| 0:02–0:03 | think-aloud priming + warm-up ("koi bhi app kholiye"); note their baseline tap speed | §10 S2 |
| 0:03–0:04 | **trust question, before** — verbatim, no reaction | §10 S3 |
| 0:04–0:06 | **T1 check-in** + SEQ | §11 T1 |
| 0:06–0:08 | T2 roster + SEQ | §11 T2 |
| 0:08–0:11 | T3 offline — *you* turn airplane mode on, visibly + SEQ | §11 T3 |
| 0:11–0:14 | **T4 who viewed my data** + SEQ | §11 T4 |
| 0:14–0:17 | T5 withdraw consent + SEQ, then re-run T2 for the §13 A check | §11 T5 · §13 A |
| 0:17–0:18 | **trust question, after** — the identical sentence; then §8 items 1 and 2 only | §10 S6 · §8 |
| 0:18–0:20 | close: withdrawal offer, thanks | §10 S8 |

**T6 (voice) is dropped from the 20-minute run.** Run it only in a full 45-minute session.

### Five rules you must not break

1. **Never touch the phone during a task.** If you touch it, the task is assist level 5 and it is a fail. Point with your eyes, not your hand.
2. **Never say the name of the thing they are looking for.** The label is what we are testing.
3. **Never answer "is this compulsory?"** — ask what they expect, then write down that they asked. That question *is* the finding (§13 B.1).
4. **Never fill the silence.** Count to fifteen before you probe. Most findings live in the seventh second.
5. **If the participant becomes upset, stop.** No probing, no next task, no clinical words in the notes. Offer to end, hand the 14416 card, write only "session ended early at participant's comfort", and tell neel and kv the same day (§10 S8).

### If something goes wrong

| Situation | Do this |
|---|---|
| the app crashes, or a chunk fails to load | stop the clock, log it as a finding, hard-reload. If it repeats, **end the session** and tell neel — a broken build wastes a participant |
| someone senior walks in | stop, close the app, resume only after they leave. Tick §13 B.8 and mark the session **void**; reschedule |
| the participant cannot read romanised Hindi | do **not** read the screen aloud for them. Note it (§15.1), let them do what they can, and log an **S2** i18n finding (§14.3) |
| they ask who you report to | answer honestly and completely (§10 S4). Never be vague — every trust measure in the session depends on you being believed |
| you fall behind the clock | drop T5. **Never** drop T1 or T4 |
| you are unsure of a severity | leave it blank. neel assigns it in the review (§9.1) |

### Afterwards (5 minutes, same day)

Fill the §15.3 rows while the session is fresh · upload the recording to the team drive under the session ID · message neel the count of S1/S2 candidates · **do not edit `executable/board.md`** — kv owns it (§9.2).

## Links

[ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [prd.md §3 NFR-04](../product/prd.md#3-non-functional-requirements) · [F02](../features/F02-jawan-app.md) · [F03](../features/F03-on-device-signals.md) · [design.md](../architecture/design/design.md) · [design-client-apps.md](../architecture/design/design-client-apps.md) · [personas.md](../product/personas.md) · [adoption-strategy.md](../product/adoption-strategy.md) · [test-plan.md](test-plan.md)

**External instrument cited:** the SEQ (Single Ease Question), Sauro & Dumas, *Comparison of three one-question, post-task usability questionnaires*, CHI 2009 — used unmodified so results stay comparable across sessions and with published work. Every other number in this document is either measured from this repo's code (§14.2) or labelled a reasoned target with a confidence rating (§12); nothing here is an invented statistic (AGENTS.md rule 7).

**Code reviewed for §14** (state as of 2026-09-09, commit `49d0492` + working tree; re-verified against the working tree after the parallel `packages/ui` and i18n landings of the same day — `Icons.tsx` was appended to only, so every line number cited in §14.1 still resolves): `web/packages/ui/src/{Icons,CareStateChip,CheckInCard,BottomTabs,SyncPill,Button}.tsx` · `web/packages/ui/src/ui.css` · `web/packages/tokens/src/tokens.json` · `web/packages/tokens/dist/tokens.css` · `web/apps/jawan/app/**` · `web/packages/i18n/src/{en,hi}.json`.
