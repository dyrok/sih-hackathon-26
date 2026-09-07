# Personas — SAARTHI

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05

Five roles, one product. The jawan is the primary persona — every other role exists only to serve the loop that ends with them. Each persona is defined by **what they see and what they never see**, because visibility boundaries *are* the product ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md): two-tier output, k ≥ 5, architectural welfare firewall). All user-facing strings below ship via i18n keys (`en`/`hi`) — see [design.md §8](../architecture/design/design.md).

## 1. Jawan / Constable — PRIMARY

| Field | Detail |
|---|---|
| Who | Constable, 34, 3rd Bn — the demo persona seeded by [FR-20](prd.md#3-scope). 10+ years in, deployed away from family, lives in unit lines. |
| Context | Extended deployments, cancelled leaves, 47+ consecutive duty days in bad stretches. Low-end Android (API 26+), poor connectivity in deployment zones, mixed literacy, Hindi-first ([ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md)). |
| Pressures | Duty load + family separation + career friction; stigma — admitting stress reads as weakness in uniform; fear that any "report" becomes an ACR entry. |
| What they see | Own data only: roster, leave, pay slip, canteen, grievance, family welfare schemes ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)); the 10-second check-in card (`checkin.prompt` — "Aaj kaisa laga?"); own 90-day trend; consent panel; the who-viewed-my-data receipt ([design.md §5](../architecture/design/design.md)). |
| What they never see | Anyone else's data — no peer scores, no unit leak-through of an individual, no "who else flagged". |
| Goals | Leave when owed; family kept informed; finish duty safely; be read as fit, not fragile. |
| Fears | A score becoming a file note; quiet transfer to "light duty" without explanation; the app being a discipline tool in disguise. |
| Quote | "Sir, sab theek hai — bas thaka hua hoon." (The masking answer — [FR-07](../features/F04-risk-rules-engine.md) exists precisely because this sentence is the default.) |

## 2. Counsellor

| Field | Detail |
|---|---|
| Who | Force counsellor/psychologist covering multiple battalions; thin coverage, limited weekly hours. |
| Context | Case load arrives as names on paper or walk-ins; no shared signal layer with the unit; sessions scarce, follow-up rarer. |
| What they see | Pseudonymized case queue ranked by urgency × intervenability; evidence cards with top-3 factor chips and source labels; full record only after dual-key unmask (with welfare officer), every unlock logged ([FR-12](../features/F06-counsellor-console.md), [FR-16](prd.md#1-users--roles)); session notes + outcome tracking. |
| What they never see | Command hierarchy views, appraisal data, or identities before unmask. |
| Goals | Reach the right person before crisis; spend scarce hours on highest-need cases; see recovery, not just referral. |
| Fears | Missing the one who mattered (false negative); alert flooding; being reduced to a rubber stamp on someone else's list. |
| Quote | "Give me evidence I can act on in one sitting — not a number to decode." |

## 3. Welfare Officer

| Field | Detail |
|---|---|
| Who | Uniformed officer handling unit welfare; the bridge between jawans and command. |
| Context | Runs welfare schemes, leave boards, family liaison; must show visible welfare wins without becoming the enforcement arm. |
| What they see | Individual evidence for *assigned* cases; intervention tracker; roster-swap proposals minimising max individual load ([FR-11](../features/F05-intervention-engine.md)); Tele-MANAS (14416) handoff records. |
| What they never see | Raw journal text without consent; anything outside assigned cases. |
| Goals | Fix workload causes, not symptoms; defensible, documented welfare actions; unit-level wins. |
| Fears | Peers reading welfare outreach as policing; wrong person, wrong intervention; being accountable for data they cannot control. |
| Quote | "I want the *reason* on the card, so my action has a paper trail that protects the jawan too." |

## 4. Commander

| Field | Detail |
|---|---|
| Who | CO / commandant — accountable for unit readiness **and** welfare; decides rosters, leaves, postings. |
| Context | Currently detects distress by manual observation ("who stopped eating in the mess") — late, biased, unscalable (PS verbatim). |
| What they see | Unit aggregates only (k ≥ 5), morale index, leading/lagging indicators, group-level trauma-exposure flags, what-if simulator ("extend Coy B by 30 days → projected fatigue +18%") ([F07](../features/F07-commander-dashboard.md)). |
| What they never see | Any individual name or score — the API rejects personnel-ID lookups for welfare data at route level; the dashboard UI has no individual-row pattern at all ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md), [design.md §4](../architecture/design/design.md)). |
| Goals | Readiness without attrition; act early on workload, not rumours; defensible welfare decisions. |
| Fears | An aggregate that hides a crisis; losing perceived control of unit information — countered by aggregates + what-if giving *action* without identity. |
| Quote | "Show me the unit's pressure so I can fix the duty chart — the individual matters belong to the counsellor." |

## 5. MHA / CRPF Evaluator

| Field | Detail |
|---|---|
| Who | Ministry/CRPF officer in the jury room and later in the pilot-decision chair. |
| Context | Judges on the PS's own six technical challenges; has seen pilots die after the hackathon; carries legal exposure for personnel data. |
| What they see | Demo environment on synthetic data; audit architecture; DPDP 2023 + MHA 2017 compliance mapping; on-prem/air-gap deployment story. |
| What they never see | Live personnel data — ever. |
| Goals | Something a havildar would voluntarily use in Hindi on a cheap phone; indigenous, deployable, legally defensible ([research](research-sih-2026.md#7-ps-26186-specific-strategy-risks--preemptions)). |
| Fears | Another dashboard nobody uses; a tool that creates liability; welfare tech that quietly becomes disciplinary tech. |
| Quote | "Prove the firewall in the architecture, not in the pitch." |

## Cross-persona tensions (by design)

| Tension | Resolution |
|---|---|
| Commander wants individuals; firewall forbids it | Aggregates + what-if give action without identity; individual tier is the counsellor's |
| Counsellor needs identity; jawan needs safety | Dual-key unmask + logged reason + subject-visible receipt |
| Welfare officer needs reach; jawan fears reach | Consent-gated journal text; assigned-cases-only scoping |

## Links

[prd.md](prd.md) · [adoption-strategy.md](adoption-strategy.md) · [F02](../features/F02-jawan-app.md) · [F06](../features/F06-counsellor-console.md) · [F07](../features/F07-commander-dashboard.md) · [rbac-matrix.md](../compliance/rbac-matrix.md)
