# Manan's work log

> Owner: manan (compliance research assistant · 1st year) · Branch: `manan`
> Files I own: `docs/compliance/sources.md` · this log.
> I do not rewrite kv/neel compliance docs. Findings for them go here.
> Frame: engineering notes, not legal advice. India's law is **DPDP Act 2023** — never "PDPA".

---

## Task PRIV-005 — Statute sources pack

- **Task ID:** `PRIV-005`
- **Due:** 2026-09-10
- **Target:** [`docs/compliance/sources.md`](../../docs/compliance/sources.md)
- **Date:** 2026-09-08
- **Status:** pack filled on branch `manan`. Waiting on kv review / merge.

### What I did

Copied the **exact** text of:

- DPDP Act 2023 **§7(i)** (and the rest of §7 so (i) is not out of context)
- DPDP Act 2023 **§§4–6** (board row says §4–5; the template also asks for withdrawal, which is **§6(4)–(6)**)
- Mental Healthcare Act 2017 **§23(1)–(2)(a)–(g)**

plus, labelled as adjacent, MHCA **§24(2)** (electronic / digital confidentiality). That sentence is what people sometimes want when they look for a "§23(3)".

### Official hosts vs what this machine could open

| Official locator | Result 2026-09-08 |
|---|---|
| https://www.indiacode.nic.in/handle/123456789/22412 (DPDP) | `Access Denied` (Akamai) |
| https://www.indiacode.nic.in/bitstream/123456789/22412/1/a2023-22.pdf | `Access Denied` |
| https://www.meity.gov.in/static/uploads/2024/01/Digital-Personal-Data-Protection-Act-2023.pdf | `Access Denied` |
| https://www.indiacode.nic.in/handle/123456789/8814 (MHCA) | `Access Denied` |
| Goa Gazette MHCA scan https://www.goa.gov.in/wp-content/uploads/2022/12/Mental-Health-Act-2017.pdf | PDF downloaded (310,661 bytes); two-column scan, OCR unusable |

Secondary locators that reproduced Gazette lettering and were used for the quotes:

- CADP DPDP text: https://cadp.in/resources/official-texts/dpdp-act-2023/ (clauses numbered `1.–9.` instead of `(a)–(i)`)
- courtbook DPDP: https://courtbook.in/bare-acts/digital-personal-data-protection-act-2023 (lettering preserved)
- Indian Kanoon DPDP §7: https://indiankanoon.org/doc/62814281/
- Indian Kanoon MHCA entire Act: https://indiankanoon.org/doc/14507371/
- Indian Kanoon MHCA §23: https://indiankanoon.org/doc/110040215/

**Ask kv:** open the Gazette / India Code PDF on a network that is not Akamai-blocked and tick the quotes in `sources.md` before any formal legal review. Secondary hosts are locators, not the statute.

### Findings for kv (I did not edit kv's files)

1. **There is no MHCA §23(3).** Section 23 has two subsections. The next section is 24. [`docs/compliance/mental-healthcare-act-2017.md`](../../docs/compliance/mental-healthcare-act-2017.md) currently says “**§23(3):** the Central Mental Health Authority is to frame confidentiality guidelines.” That number is a mis-cite. Central Authority procedure / guideline powers sit elsewhere (e.g. §6 manner of advance directive, §12 review of advance directives). Digital-record confidentiality is **§24(2)**.
2. kv’s DPDP map writes “§4(a)” as shorthand for **§4(1)(a)**. The Act’s lettering is `4(1)(a)` consent / `4(1)(b)` certain legitimate uses. Fine as shorthand; the sources pack uses the Act’s numbering.
3. CADP renders §7 clauses as `1.–9.`. The Gazette / courtbook / Indian Kanoon use `(a)–(i)`. Quotes in `sources.md` use letters.
4. Indian Kanoon / courtbook §7(b) illustration has a likely transcription glitch (“personal data of X processing to determine”). Operative clauses `(a)–(i)` match across CADP, courtbook and Indian Kanoon. I quoted the operative clauses, not that illustration.

### One-liners for risa (copy from `sources.md` only)

Already listed at the bottom of `sources.md`. Do not rewrite.

---

## Task PRIV-006 — Manual privacy walkthrough

- **Task ID:** `PRIV-006`
- **Due:** 2026-09-15
- **Depends on:** APP-004 (neel) — consent flow + silent withdrawal **in the jawan app**. APP-005 is the who-viewed **screen**.
- **Date of this pass:** 2026-09-08
- **Status:** API pass recorded below. **UI click-through is blocked** until neel ships APP-004 / APP-005.

This is not legal advice. It is a pass/fail of the v1 API against the three flows the task names: consent given, consent withdrawn, who-viewed-my-data.

### UI click-through (the actual task) — BLOCKED

| Step | Where (once the app exists) | Result |
|---|---|---|
| Open jawan app as Constable 34, 3rd Bn | APP-004 | **BLOCKED** — no Expo app yet (APP-001 still `[ ]`) |
| Grant unbundled consent (check-in / instruments / voice) | Me → consent sheet | **BLOCKED** APP-004 / neel |
| Withdraw at the same tap depth; confirm command dashboard does not change | Me → withdraw | **BLOCKED** APP-004 / neel |
| Open who-viewed-my-data; see role, when, why | Me → receipts | **BLOCKED** APP-005 / neel |

Re-run this table when APP-004 is `[x]`. Until then the board row is `[!] APP-004/neel`.

### API walkthrough (what I could run today)

Method: FastAPI `TestClient` against a fresh seeded SQLite demo (`jawan.demo` / `counsellor.a` / `welfare.a` / `commander.3bn`, password `saarthi`). Same seed as `python -m app.seed`. Not a long-lived `localhost:8000` (nothing was bound); the client hits the same app object uvicorn would serve.

Persona: Constable 34, 3rd Bn — `jawan.demo` → pseudonym `ps_demo01` / personnel `CR-DEMO-01`.

| # | Step | Call | Expected | Got | Result |
|---|---|---|---|---|---|
| 1 | Jawan grants a new unbundled bundle | `POST /app/consent` `{bundle_id: voice, purpose_string: on_device_features, data_categories: [voice_features], language: hi}` | 200 + `consent_id` | 200 `cn_e8a301cedbab` / `voice` | **PASS** |
| 2 | Who-viewed before any counsellor open | `GET /app/who-viewed` as jawan | 200, empty or no counsellor `risk.read` | 200, `entries: []` | **PASS** |
| 3 | Counsellor opens the case | `GET /risk/ps_demo01` as `counsellor.a` | 200, score + tier, **no legal name** | 200, score 42, tier `amber`, keys have `pseudonym_id` not `legal_name` | **PASS** |
| 4 | Who-viewed after that open | `GET /app/who-viewed` as jawan | counsellor + when + why | 1 entry: role `counsellor`, action `risk.read`, why `counsellor/welfare case view` | **PASS** |
| 5 | Judge's attack: commander looks up a person | `GET /welfare/personnel/CR-DEMO-01` as `commander.3bn` | always 403 | 403 `commander identity cannot access individual welfare data (ADR-0003)` | **PASS** |
| 6 | Commander asks for an individual score | `GET /risk/ps_demo01` as commander | 403 | 403 same firewall text | **PASS** |
| 7 | Commander unit heatmap before withdraw | `GET /aggregates/unit/3BN` | 200, k ≥ 5, no consent field | 200, `k: 5`, `n: 12`, no `consent` / `withdraw` in payload | **PASS** |
| 8 | Silent withdrawal | `POST /app/consent/withdraw` as jawan | 200, `command_visible: false` | 200 `{withdrawn: 4, command_visible: false}` (3 seed bundles + the voice grant) | **PASS** |
| 9 | Commander heatmap after withdraw | `GET /aggregates/unit/3BN` again | visually unchanged; still no consent field | `k` still 5; still no `consent` / `withdraw` | **PASS** (silent) |
| 10 | Unmask must die without a live artefact | `POST /privacy/unmask` as counsellor after withdraw | 403 | 403 `unmask requires an active consent artefact` | **PASS** |
| 11 | Re-grant check-in so dual-key can be shown | `POST /app/consent` bundle `checkin` | 200 | 200 | **PASS** |
| 12 | Counsellor alone cannot see identity | open unmask, then `GET /privacy/unmask/{id}/identity` | 403 until second key | request `pending`; identity 403 `no active unmask grant` | **PASS** |
| 13 | Welfare officer supplies the second key | `POST /privacy/unmask/{id}/approve` as `welfare.a` | granted | 200 `status: granted` | **PASS** |
| 14 | Identity is then visible to a keyholder | `GET .../identity` as counsellor | personnel id of the persona | `CR-DEMO-01` / `Demo Constable` / Constable / 3BN | **PASS** |
| 15 | Subject sees the unmask | `GET /app/who-viewed` | `unmask.grant` and/or `identity.read` | both present; roles `counsellor` + `welfare_officer` | **PASS** |

Matching automated tests (2026-09-08, `cd backend && pytest -q tests/test_privacy.py tests/test_firewall.py tests/test_persona_and_harness.py::test_who_viewed_after_counsellor_read`): **16 passed**.

### Notes from the walkthrough (for kv / neel, not edits)

- `GET /app/who-viewed` does **not** list `consent.grant` or `consent.withdraw`. The feed is the subject-visible slice of counsellor / welfare / break-glass / unmask actions (`privacy.py` allow-list). That matches F08 (“who opened their record”), not a consent ledger. If the app UI needs “you withdrew at time T”, that is a different endpoint or the UI reads consent artefacts directly — flag for neel when APP-005 is designed.
- The personnel-id trap `GET /welfare/personnel/{id}` is 403, but the body I got was the **firewall middleware** string (`commander identity cannot access individual welfare data`) rather than the handler’s own `no personnel-id welfare lookup exists (ADR-0003)`. Still closed. kv can decide whether the demo script should show the trap copy (would need the firewall to let commanders hit that one route).
- Withdrawal is one call that withdraws **all** live bundles (`withdrawn: 4`). DPDP §6(1) wants purpose-specific consent; unbundled grant exists, but unbundled *withdrawal* of a single bundle is not a separate route. Flag for kv if a per-bundle withdraw is wanted before APP-004.
- After withdraw, unmask is refused. Counsellor can still `GET /risk/ps_demo01` (pseudonym + score). That is the residual kv already logged in PRIV-004 (“score on a pseudonym”). I did not change it.

### How to re-run when APP-004 lands

1. `cd backend && python -m app.seed && uvicorn app.main:app --port 8000`
2. Point the Expo app at `http://127.0.0.1:8000`.
3. Login `jawan.demo` / `saarthi`.
4. Tick the UI table above: grant → who-viewed empty of counsellor → ask someone to open the counsellor console on `ps_demo01` → who-viewed shows the open → withdraw → commander heatmap unchanged.
5. Flip this board row from `[!]` to `[x]` only after those taps exist.

### Curl cheat-sheet (same calls as the table)

```bash
# login
J=$(curl -s http://127.0.0.1:8000/auth/login -H 'content-type: application/json' \
  -d '{"username":"jawan.demo","password":"saarthi"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
C=$(curl -s http://127.0.0.1:8000/auth/login -H 'content-type: application/json' \
  -d '{"username":"counsellor.a","password":"saarthi"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
M=$(curl -s http://127.0.0.1:8000/auth/login -H 'content-type: application/json' \
  -d '{"username":"commander.3bn","password":"saarthi"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s http://127.0.0.1:8000/app/consent -H "authorization: Bearer $J" -H 'content-type: application/json' \
  -d '{"bundle_id":"voice","purpose_string":"on_device_features","data_categories":["voice_features"],"language":"hi"}'
curl -s http://127.0.0.1:8000/app/who-viewed -H "authorization: Bearer $J"
curl -s http://127.0.0.1:8000/risk/ps_demo01 -H "authorization: Bearer $C"
curl -s http://127.0.0.1:8000/app/who-viewed -H "authorization: Bearer $J"
curl -s -o /dev/stderr -w "%{http_code}\n" http://127.0.0.1:8000/welfare/personnel/CR-DEMO-01 -H "authorization: Bearer $M"
curl -s http://127.0.0.1:8000/app/consent/withdraw -H "authorization: Bearer $J" -X POST
```

---

## Requests for kv

1. Re-verify `sources.md` quotes against the Gazette PDF (official hosts were blocked here).
2. Fix the §23(3) cite in `mental-healthcare-act-2017.md` (kv-owned) — I did not touch it.
3. Review this branch and merge to `main` when happy. I will not merge it.
4. After APP-004: ping me to re-tick the UI table and then set PRIV-006 `[x]`.
