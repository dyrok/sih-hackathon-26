# F02 — Jawan App (roster-first voluntary check-in, consent, transparency)

> Owner: neel · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-02, FR-04, FR-15, FR-19 in [prd.md](../product/prd.md) (FR-17 silent withdrawal surfaces here, owned by [F08](F08-privacy-safety-architecture.md)) · [Architecture](../architecture/architecture.md) · [Design system](../architecture/design/design.md)

## Purpose
The app personnel already open daily — duty roster, leave, pay slip — with a 10-second wellness check-in riding on that home screen ([ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md)). Zero adoption ask; welfare data rides an existing habit. The app is never branded as therapy: framing is "fitness for duty" + "parivaar welfare". It is also where trust is demonstrated rather than promised: unbundled consent, silent withdrawal, and who-viewed-my-data receipts.

Adoption guardrails (what makes participation real rather than coerced):
- Non-participation contributes zero priority points; the app never threatens, nags, or counts streaks.
- Unit-level rewards only — no individual incentives, which would falsify data.
- Officer-first rollout: commandants take the check-in publicly before the unit is asked to.
- A 10-second daily check-in is the core loop; full instruments are monthly, never the entry price.

## User-visible behavior (screen by screen)
1. **Home (roster-first).** Cards: duty roster (`roster.view`), leave application, pay slip, canteen, grievance, family welfare schemes — F01/HRMS-backed surfaces. Below them one calm card: "Aaj kaisa laga? (10 second)" (`home.checkin.title`). No badge, no streak counter, no guilt mechanics (anti-pattern per ADR-0004).
2. **Check-in sheet.** Bottom sheet: emoji row (5 states, `checkin.emoji.*`) → one slider (0–10, `checkin.slider.label`) → submit. Optional free text with mic (voice capture path is F03). Hard budget: ≤ 3 taps, no network required (FR-04).
3. **Monthly instrument.** One validated instrument per month, rotated from the bank — PHQ-9, GAD-7, PSS-10, ISI (core per FR-02), plus Maslach Burnout and PCL-5 (bank extension; PRD FR-02 text to be extended in the same PR that lands them). One question per screen, icon + text, progress dots. Disclaimer every time: "Ye jaanch salahn hai, nidan nahi" (`screen.disclaimer`). **Validated instruments only — zero invented questions.** Scales are translated **and culturally adapted** (clinician-reviewed back-translation, idiom substitution, re-anchored response options, recorded voice prompts) — a literal translation of Western scales scores wrong. Hindi + English at launch; regional languages are i18n data files, not redesigns (design.md §8).
4. **My trend.** Personal 90-day TrendLine against own baseline. No peer comparison, no unit ranking, ever.
5. **Consent panel.** Unbundled scopes (`consent.scope.checkin/.instrument/.voice/.passive/.pulse/.buddy`), each with a plain-language purpose line. Withdrawal is the same tap depth as granting, takes effect immediately, and is **silent**: nothing command-visible changes (FR-17).
6. **Who viewed my data.** Receipt timeline: role chips, timestamp, purpose string from the audit log, access duration; unmask events render in the same list ("Counsellor + Welfare Officer opened your case on 12 Sep — reason: Red-tier outreach"). Header: "Aapka data. Aapka adhikar." (`receipt.header`). The most important 15 seconds of the product.
7. **Battle buddy.** Pair with one colleague; both see each other's coarse status only (`buddy.state.ok|quiet|sos`). `sos` offers one tap to the buddy's unit JCO contact and the 14416 line. Command sees neither side of any pairing.
8. **Unit pulse.** Rate command climate 1–5 on fixed facets (leadership, fairness of duties, family support, facilities). One rating per member per period; only the k ≥ 5 aggregate surfaces (FR-19), and it surfaces to commanders (F07), not back into the app.
9. **Settings.** Language, voice prompts, sync status (SyncPill), pause/withdraw each data scope.

## Data model (fields, units, consent tags)
| Table | Key fields | Consent tag |
|---|---|---|
| `check_in` | `pseudonym`, `local_date`, `mood_emoji` (1–5), `stress_slider` (0–10), `free_text?`, `captured_at`, `synced_at` | `checkin` |
| `instrument_response` | `instrument` (phq9/gad7/pss10/isi/mbi/pcl5), `item_index`, `raw`, `total`, `validity_items[]`, `taken_at` | `instrument` |
| `consent_record` | `scope`, `granted_at`, `consent_version`, `withdrawn_at` | self-referential |
| `unit_pulse` | `period`, `facet`, `rating` (1–5) | `pulse` |
| `buddy_pair` | `pair_id`, `a_pseudonym`, `b_pseudonym`, `coarse_state` | `buddy` |
| `access_receipt` (server, read-only here) | `viewer_role`, `purpose_code`, `accessed_at`, `duration_s`, `unmask_event?` | n/a (transparency) |

Pseudonym is the only identifier on the wire; the pseudonym→identity map never reaches this app (F08). `free_text` syncs only under `checkin` consent; voice transcripts are kept only if the user keeps them.

i18n keys introduced by this feature (design.md §8 — all strings ship via keys, never literals):
| Key | `en` | `hi` |
|---|---|---|
| `home.checkin.title` | "How was today? (10 seconds)" | "Aaj kaisa laga? (10 second)" |
| `screen.disclaimer` | "This is reflection support, not diagnosis." | "Ye jaanch salahn hai, nidan nahi" |
| `receipt.header` | "Your data. Your right." | "Aapka data. Aapka adhikar." |
| `sync.pill.queued` | "{n} check-ins saved, will send" | "{n} check-in save hue, bhejenge" |
| `sync.error.recovery` | "Sync failed. Your data is safe, we'll retry." | "Sync nahi hua. Data safe hai, dobara try karenge." |
| `home.checkin.empty` | "First check-in — takes 10 seconds." | "Pehli baar check-in — 10 second lagenge." |
| `instrument.done` | "Done for this month" | "Is mahine ho gaya" |
| `buddy.state.*` | ok / quiet / need a word | theek / thoda chup / baat karo |

## API surface (endpoints, role-scoped)
Role `jawan`; every endpoint resolves the subject from the auth token — no client-supplied personnel ID is accepted (403 otherwise).
- `POST /v1/checkins` — batch sync of queued items, idempotent by `client_uuid`
- `POST /v1/instruments/responses` — server rejects an instrument already taken this month
- `GET /v1/me/trend` — own data only
- `GET /v1/me/access-receipts` — feeds screen 6
- `GET /v1/me/consents` · `PUT /v1/me/consents` — withdrawal must produce no command-visible side effect (FR-17 test)
- `POST /v1/pulse/ratings` · `GET /v1/pulse/aggregate` — k ≥ 5 enforced server-side
- `GET/POST /v1/buddy/status` — coarse enum only
- Roster / leave / payslip endpoints are thin read proxies over F01 ingested data.

## States (idle/loading/empty/error/offline)
- **Offline:** check-in writes to local SQLite instantly; SyncPill: "3 check-ins saved, will send" (`sync.pill.queued`) — queued data never renders in error styling (ADR-0005). Instruments run fully offline; sync resumes opportunistically.
- **Empty:** first-run teaching copy: "Pehli baar check-in — 10 second lagenge" (`home.checkin.empty`).
- **Error:** recovery paths, never blame: "Sync nahi hua. Data safe hai, dobara try karenge." (`sync.error.recovery`).
- **Already done / disabled:** instrument card shows "Is mahine ho gaya" (`instrument.done`); buddy slot empty state explains pairing in one line.
- **Conflict:** re-submitted check-in for the same local day is a no-op server-side; the client keeps the earliest capture.

## Privacy notes (what this feature must never do)
- Never expose an individual risk score, badge, or ranking to anyone in the command chain — no such endpoint exists (ADR-0003 firewall; see F07).
- Never gamify or incentivise individually — unit rewards only; a coerced check-in is a falsified data point.
- Never reveal who withdrew consent, via any endpoint, aggregate denominator, or participation count.
- Never let one token address another jawan's data — self-scope is the only query shape.
- Never brand anything as therapy, counseling, or "problem detection" in copy or screenshots.
- Raw free text is visible to no one in the chain; counsellor access requires consent + dual key (F06/F08) and is receipted.
- No PII (name, service number) travels with wellness payloads; screenshots for demo decks must use synthetic data (F09).

## Out of scope / non-goals
Diagnosis or treatment; clinician chat; social feed or peer ranking; streaks/leaderboards; iOS (ADR-0005); wearable pairing (F03 owns the surface); ambient listening (F03/ADR-0002 anti-goal); regional language translation at v1 (keys reserved); HR workflow authoring (leave approval stays in existing HRMS).

## Definition of done
- [ ] 10-second check-in completes offline on an API 26 low-end device; queued sync verified across an airplane-mode toggle, zero duplicates.
- [ ] All six instruments ship with adapted `hi`/`en` strings + recorded voice prompts; adaptation review signed off; zero invented items.
- [ ] Unbundled consent works end to end; automated test proves withdrawal leaves zero command-visible trace on F08 endpoints.
- [ ] Access receipts render every real audit event (including unmask) within one sync cycle.
- [ ] Unit pulse aggregate suppresses cells with < 5 contributors server-side.
- [ ] All strings via i18n keys; Devanagari line-height rule holds (design.md §3); check-in measured at ≤ 3 taps on device.

## Links
[ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) · [ADR-0004](../architecture/decisions/0004-roster-app-first-adoption.md) · [ADR-0005](../architecture/decisions/0005-offline-first-low-end-android.md) · [F03](F03-on-device-signals.md) · [F04](F04-risk-rules-engine.md) · [F05](F05-intervention-engine.md) · [F08](F08-privacy-safety-architecture.md) · [adoption-strategy.md](../product/adoption-strategy.md) · [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md) · [mental-healthcare-act-2017.md](../compliance/mental-healthcare-act-2017.md)
