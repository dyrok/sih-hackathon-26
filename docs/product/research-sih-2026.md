# SIH 2026 Winning Research — PS 26186 (AI-Based Predictive Personnel Stress & Welfare Monitoring, CRPF / MHA)

> Owner: kv · Status: [x] frozen (raw research — source material for [winning-strategy.md](winning-strategy.md)) · Last updated: 2026-09-05

Research date: 2026 (primary sources include the official SIH 2026 Guidelines PDF and the official SIH Evaluation Guideline PDF).

---

## 1. PS 26186 at a glance (official text, sih.gov.in)

- **Org/Dept:** Ministry of Home Affairs — Central Reserve Police Force (CRPF), Police II Division
- **Category/Theme:** Software — MedTech / BioTech / HealthTech
- **Idea submission window:** portal opens Aug 2026; **hard deadline 20 Sep 2026**; max **500 ideas per PS**, then frozen
- **Dataset offered:** anonymized HR datasets, deployment records, leave history, wellness survey data, workload data, simulated behavioral datasets
- **Team competition status (as scraped 2026-08-24): 0 / 500 ideas submitted** → low-competition window still open
- **What CRPF asked for:** predictive behavioral analytics engine; mobile wellness/self-assessment app; commander + welfare-officer dashboards; intervention recommendation system; HRMS integration; privacy-preserving analytics; RBAC; anonymization/secure storage; alerts for authorized welfare personnel
- **Explicit constraints in the PS:** welfare (non-disciplinary) focus; dignity/confidentiality; stigmatization prevention; FP/FN minimization; ethical transparent AI; personnel trust
- **Strategic importance verbatim:** "Creates an **indigenous capability** tailored to the unique operational and cultural environment of Indian CAPFs and Armed Forces"

---

## 2. SIH 2026 structure & deadlines (official Guidelines PDF, sih.gov.in/letters/2026)

| Stage | Facts |
|---|---|
| SPOC registration | July 2026 (college Single Point of Contact registers; students CANNOT self-register) |
| Internal hackathon | College-run, Aug–Sep 2026; SPOC nominates top teams: **max 50 per institute (45 shortlisted + 5 waitlisted)**, 100 for universities |
| Idea submission | Portal opens Aug 2026; team leader verifies pre-entered team data and submits: team name, authorization letter PDF (college letterhead, principal-signed, 6 members + up to 2 mentors), chosen PS, **idea title, idea description, idea presentation (PDF)**; deadline **20 Sep 2026**; **max 2 PS per team**; 500-idea cap per PS |
| National screening | Experts shortlist **4–5 teams per problem statement**; notified via portal + email; teams "will be available for meetings, sessions and trainings during preparation phase" |
| Grand Finale | **Offline at nodal centers across India, December 2026**; only registered 6 students + up to 2 mentors allowed on venue; travel reimbursement ₹3,000/person |
| Mentors | Up to 2 (industry/academia, 5+ yrs experience) selected by team post-shortlist |
| Prize | **₹1,50,000 per problem statement, ONE winner per PS** — "prize money will be given by the collaborating ministry/industry ONLY IF that organization likes the idea"; final decision rests with PS-creating organization |
| IP | IP of winning ideas split between the industry/government that posed the PS and the winning team (mutual agreement); ideas must be NEW and never presented in any previous event/program |

**Idea selection (national screening) criteria, verbatim from SIH 2026 guidelines:** "novelty of the idea, complexity, clarity and details in the prescribed format, feasibility, practicability, sustainability, scale of impact, user experience and potential for future work progression."

---

## 3. Official evaluation rubric (Evaluation Guideline PDF, siceval.mic.gov.in — carried across editions; 3 evaluators score each round 1–20 per criterion, 100 per round)

### Round 1 — Idea presentation (weight 20%)
1. Presentation of the Solution/Idea (fit to PS/theme)
2. Innovation (uniqueness & creativity)
3. Solution Approach (roadmap/framework)
4. Technical Soundness / Feasibility
5. Execution Timeline for Hackathon (blueprint of prototype completion vs. 36h)

### Round 2 — Prototype progress evaluation (weight 30%)
1. Prototype Development (progress toward working prototype)
2. Improvement (changes based on evaluator/mentor feedback)
3. Integration (components working together)
4. Usability
5. Teamwork (contribution of individual members)

### Round 3 — Final demo (weight 50%)
1. Functionality / Relevance to problem statement
2. Performance / Final Demo (real-world effectiveness + clarity & persuasiveness of presentation)
3. UX / Aesthetics / Design / Ergonomics
4. Market readiness / Impact
5. Implementation plan / Future scope

**Final score = weighted 20 / 30 / 50 across 3 independent evaluators → 100 max.** The finale alone is half your total; but Round 1+2 (50%) are scored on presentation and mid-build checkpoints, so deck + responsiveness to mentor feedback still decide outcomes.

---

## 4. Round-by-round jury expectations (from official docs + winner accounts)

### Internal college round (steep cut — 60–80% of teams die here)
- ~3-minute pitch to faculty panel; 6 members, ≥1 female mandatory
- What clears the cut: 10-second clickable mockup (Figma/v0), clean architecture diagram, clear role split (each member answers their domain), 36-hour feasibility plan with hours attached, respectful "incorporated in Phase 2" handling of doubts
- Killer mistakes: wall-of-text PPTs, promising AI+Blockchain+IoT together, one member talking while others stand silent, defensive arguing
- Working prototype ≠ mandatory but is a differentiator: "we were the only team with a functioning prototype at the internal stage" (winner account)

### National screening (idea submission)
- Evaluators read the PDF idea deck cold (title, description, presentation). Judged on novelty, complexity, clarity in prescribed format, feasibility, sustainability, scale of impact, UX, future progression
- Deck mapped 1:1 onto the official rubric beats beautiful-but-unmapped decks
- Video demo link + prototype screenshots inside the PDF materially raise credibility

### Grand finale (36h, December 2026, nodal centre)
- Hour 0–4: architecture pre-decided, start coding immediately (winner: "Half those impressive-looking teams spent the first 2 hours arguing about architecture. We started coding at hour 1")
- Role split that won: 2 backend+DB, 2 frontend+UI, 1 AI/ML, 1 documentation+testing+demo-prep (the doc person = "secret weapon"; demo practiced at hour 20)
- Mentors evaluate mid-build (Round 2 criteria: improvement on feedback, integration, teamwork) — visibly incorporate mentor suggestions
- Final jury (Round 3): 3-minute demo script wins, 5-minute limit enforced ruthlessly (one team's 12-min pitch was cut at 5 without ever demoing)
- Winning demo formula (winner's own): 10s problem w/ one statistic → 90s live solution on real data → 20s impact ("saves X hours/week") → 20s tech depth (one architecture slide) → 10s scale ("handles 10,000 concurrent users")
- Judge's actual feedback: problem fit ("most teams built something adjacent"), live demo with real data ("made us trust it works"), robustness/edge cases. Code quality, ML accuracy, tech stack were NOT mentioned
- Operational insurance: offline/local run, recorded demo on two devices, seeded realistic Indian-context data, mobile responsiveness, PDF slides on pen drive + email, one person carries all of it, rotation sleep (2 sleep while 4 work)

---

## 5. Top 10 winning tactics (evidence-backed)

1. **Ship a working demo at every stage, ugly beats beautiful** — only team with functioning prototype cleared internals; judges "ask if it solves the problem, not if it's real ML." (Reskilll winner blog)
2. **Map the deck 1:1 to the official 3-round rubric** — 15 criteria are public (innovation, solution approach, feasibility, timeline, prototype, improvement-on-feedback, integration, usability, teamwork, functionality, demo, UX, market-readiness, impact, future scope). (siceval.mic.gov.in PDF)
3. **Pre-decide architecture; use the first 4 finale hours to build, not argue.** (Reskilll winner blog)
4. **Name the deadline reality:** internal round is the steepest cut; carry backup video/PDF/GitHub; never demo an empty dashboard — seed realistic Indian data. (Zaid Sayyed internal-round playbook)
5. **3-minute demo script, practiced 5×:** problem(10s)→live(90s)→impact(20s)→tech(20s)→scale(10s). (Reskilll winner blog)
6. **Ministry-specific differentiation answers:** vs. consumer/off-the-shelf — "ministry-specific compliance, offline-first, local language, official government data integration" — the winning script for "why yours?" (Zaid internal-round playbook, Q2)
7. **Say the failure mode before the jury does:** "What happens when your model is wrong?" → name FP/FN costs, confidence thresholds, human-in-the-loop fallback. An honest 82% with known weaknesses beats unverifiable 99%. (Zaid internal-round playbook, Q14 + Reskilll)
8. **Use the ministry's own reports for framing** — "nobody solved it yet" must be answered with the actual blocker from ministry data; cite data.gov.in / ministry publications for data sourcing. (Zaid playbook + keshavcodes)
9. **Tech buzzwords used honestly:** AI/ML/edge/NLP named naturally and implemented at least in part; be straight about pretrained vs from-scratch ("Judges ask whether it works and whether you understand the problem"). (keshavcodes + Zaid)
10. **Boundary-setting wins respect:** "What will you NOT build?" → explicit out-of-scope slide; scalable beyond pilot = non-technical scaling (onboarding, training, handover), and "who pays after the hackathon" answered with the sponsoring org. (Zaid internal-round playbook)

---

## 6. Slide deck structure (official template discipline + recommended flow)

**Rules:** use the official SIH PPT template (fonts/backgrounds/colors unmodified — "they gave you that template for a reason"); export PDF; keep it ~10–13 slides; video-demo link embedded; prototype screenshots mandatory.

1. **Title** — PS ID 26186 + title, project name (memorable), team (6, ≥1 female), institute, PS org (CRPF/MHA) & theme
2. **Problem statement** — restate in your own words + one statistic
3. **Team & roles** — names, roles, expertise (who owns data/models/app/compliance/demo)
4. **Solution overview** — the whole idea in 2–3 lines
5. **Approach/methodology** — workflow diagram anyone can follow
6. **Technology stack** — languages, frameworks, models, APIs, deployment
7. **Architecture** — data flow: HRMS signals + voluntary app data → anonymization → risk engine → role-scoped dashboards/alerts
8. **Innovation / differentiation** — vs. existing EAPs/HRIS/wellness tools; comparison table
9. **Prototype/demo** — screenshots + link; what already works today
10. **Implementation plan** — 36-hour build timeline with hours attached (Round 1 criterion #5)
11. **Impact & scalability** — measurable outcomes for CAPFs + expansion path (state police, disaster services, corporates — from PS "Potential Market")
12. **Future scope** — beyond finale; what you will NOT build now
13. **Conclusion** — one memorable number + team strength

---

## 7. PS 26186-specific strategy (risks → preemptions)

### The 6 named technical challenges (from the PS itself) map 1:1 to jury questions:
| PS challenge | Your preemption |
|---|---|
| Privacy/confidentiality of sensitive personnel data | DPDP Act 2023 architecture: Section 7(i) "legitimate use" for core HR signals (leave, deployment, duty rosters) — no consent needed; **explicit, revocable, unbundled consent UI** for voluntary self-reports/wellness surveys (Sec. 4/5: free, specific, informed, unambiguous, unconditional, withdrawal-as-easy-as-giving); multi-lingual notices; grievance officer + Data Protection Board escalation path; retention schedule + automated deletion; breach notification workflow (Draft Rules propose 72h; penalties up to ₹250 crore/instance); Significant Data Fiduciary duties (DPO, audit) because CRPF-scale processing will trigger SDF designation |
| Preventing stigmatization | Access-by-design: commander sees **only aggregated ≥5-respondent unit pulses**, never names/scores/journals; welfare officer sees case queue with source-labelled explainable evidence; personnel see who viewed their record (transparency log); scores never used for appraisal/transfer/discipline — verifiable in code, not just claimed in slides |
| False positives / false negatives | Confidence thresholds, human-in-loop welfare officer sign-off before any intervention, cost-of-error framing (FP = stigma cost, FN = missed distress), honest accuracy reporting with failure cases |
| Ethical & transparent AI | Explainable factor list per alert with source attribution (organizational record vs. voluntary wellness); rules-based/explainable engine + optionally LLM for unstructured inputs — winner account: judges never asked "is it real ML," they asked if it solved the problem |
| Cybersecurity of psychological data | Encryption at rest/in transit, on-prem/air-gapped deployment option, RBAC enforced server-side, audit logs, CSP/security headers, throttle/sign-in hardening |
| Trust of personnel | Opt-in visible to peers as zero-cost ("non-participation contributes zero priority points"), personal data-correction requests (DPDP right to correction/erasure), WHO-5/PSS-10/GAD-7/PHQ-9 screeners marked "reflection support, not diagnosis" |

### Competition intel
- A visible competitor repo (SENTINEL, by a former-SIH-winner author) already implements exactly the privacy-first role-scoped pattern: role separation (Personnel/Welfare Officer/Commander), journal privacy, aggregate suppression <5, explainable priority engine, automated regression tests, honest "not clinically validated" limitations. Match/beat this baseline: theirs is a rules prototype — beat it with **a real (small, honestly-evaluated) predictive model** on the PS-offered datasets, offline mobile app, Hindi + regional languages, and force-grade auth mock (SSO/MFA).
- Opening statistic bank for the 10-second problem hook: **281 CRPF suicides in five years, 2025 the worst year (59 deaths); CAPF suicide rate ≈13/100k vs 8.9 for educated males nationally; ~50,000 CAPF resignations in 5 years; MHA's own current measures (duty-hour regulation, leave, counselling, yoga) are reactive — your system makes them predictive.**
- "Why indigenous / Make in India" angle: PS explicitly requests "indigenous capability tailored to the unique operational and cultural environment of Indian CAPFs" — say "on-prem, air-gappable, Atmanirbhar stack, no foreign SaaS touching welfare data," and note consumer mental-health apps can't be deployed inside a CAPF (data residency + classification).
- Data story: the PS ships anonymized HR/deployment/leave/wellness datasets — use them, and model the HRMS schema on published MHA/CRPF structures; say what's simulated vs. real.

### Final-round extras for this PS
- Demo three personas end-to-end in 3 minutes: sepoy self-check-in → welfare officer gets explainable alert + intervention suggestion → commander sees aggregate-only pulse. That single walkthrough demonstrates every expected component (app, engine, dashboards, alerts, RBAC, privacy).
- Pre-write the "privacy under a defense ministry" answer: DPDP lawful-basis split, aggregation threshold, no-biometrics-by-default ("voluntary biometric data, where authorized and legally permissible" — show you know you'd need legal authority, minimization, and meaningful consent), and deployment inside force perimeter.
- Prize reality check: ₹1.5L only if CRPF/MHA likes the solution — design for the welfare officer who'll be in the jury room, i.e., a tool a havildar would actually use voluntarily in Hindi on a low-end Android phone.

---

## 8. Documentation / submission artifacts checklist

- [ ] Idea presentation **PDF** on official SIH template (submitted by team leader on portal by 20 Sep 2026; idea title + description fields)
- [ ] College authorization letter PDF (letterhead, principal-signed, 6 members + up to 2 mentors, team name unique & not containing institute name, Annexure-A format)
- [ ] Demo **video** (screen recording, link embedded in deck) — differentiator even though not formally mandatory
- [ ] GitHub repo (public, README, seeded demo data, setup in one command) — "assumes laptop won't be yours; pulled onto any machine in 5 minutes"
- [ ] Internal-hackathon report (SPOC's side; ≤15 pages: overview, teams, photos, jury panel, social-media hashtags #sih2026)
- [ ] Grand finale: college photo IDs + consent letters, stamped team photo ID from college, PDF slides + recorded demo on pen drive and two devices, local-run build, hotspot backup
- [ ] If shortlisted: choose up to 2 mentors (5+ yrs industry/academia) and use them — Round 2 scores "improvement based on mentor feedback"

---

## Sources
- Official SIH 2026 Guidelines PDF — https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf
- Official SIH Evaluation Guideline PDF (3-round rubric, 20/30/50 weights) — https://siceval.mic.gov.in/assets/img/Evaluation_Guidelines_for_sih2024.pdf
- SIH portal — https://www.sih.gov.in/
- PS 26186 full text (scraped from sih.gov.in) — https://sih2026.vuce.in/ps/SIH26186 and https://raw.githubusercontent.com/ace-ify/sih-hub/main/ps/SIH26186.md
- PS viewer (233 PS, filters) — https://sih2026-ps-viewer.vercel.app/ and https://sih2026.vuce.in/
- Zaid Sayyed, SIH 2026 Winner's Playbook — https://zaidsayyed.in/blog/sih-2026
- Zaid Sayyed, College Internal Round Playbook (viva defense, 18 jury questions) — https://zaidsayyed.in/blog/sih-2026-internal-hackathon-guide
- Reskilll, "How I Won Smart India Hackathon: Lessons from 36 Hours" — https://blogs.reskilll.com/how-i-won-smart-india-hackathon-lessons-36-hours-changed-everything/
- Keshav, "Smart India Hackathon: Journey to the Grand Finale" — https://www.keshavcodes.in/blog/smart-India-hackathon
- TheNewViews, How to Win SIH 2026 — https://thenewviews.com/how-to-win-smart-india-hackathon/
- TheNewViews, SIH 2026 FAQs — https://thenewviews.com/smart-india-hackathon-sih-2026-faqs-registration-eligibility-team-rules-more/
- TheNewViews, Internal SIH 2026 guide — https://thenewviews.com/internal-smart-india-hackathon-2026/
- TheNewViews, SIH 2026 PPT template & format — https://thenewviews.com/sih-2026-ppt-template/
- Competitor/inspiration repo SENTINEL (PS 26186) — https://github.com/ZaidCodesin/SIH2026-PS26186
- DPDP Act 2023 for HR data (legitimate use §7(i), explicit consent, SDF, penalties) — https://www.indianhrm.com/guides/dpdp-act-hr-india
- Consent framework under DPDP Act (valid consent elements, penalties ₹250cr) — https://ksandk.com/data-protection-and-data-privacy/consent-under-dpdp-act-2023-compliance-strategies/
- ThePrint, "654 suicides & 50,000 resignations in 5 years: the crisis stalking India's CAPFs" — https://theprint.in/india/654-suicides-50000-resignations-in-5-years-the-crisis-stalking-indias-capfs/1787191/
- CRPF 281 suicides in 5 years, 2025 highest — https://www.theuttamhindu.com/india/crpf-records-281-suicides-554304 ; https://www.rnamedia.in/top-story/crpf-faces-sharp-rise-in-suicides-as-59-personnel-die-in-2025/19636
- CAPF suicide-rate decade analysis — https://www.researchgate.net/publication/390532606_ANALYSIS_OF_SUICIDE_RATES_AMONG_CENTRAL_ARMED_POLICE_FORCES_CAPF_PERSONNEL_A_DECADE_OF_DATA
