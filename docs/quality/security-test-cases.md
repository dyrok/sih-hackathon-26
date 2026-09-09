# Security Test Cases — SAARTHI (TC-410 … TC-460)

> Owner: neel · Status: [x] complete · Last updated: 2026-09-09
> Related: [test-plan.md](test-plan.md) §4/§9 · [threat-model.md](threat-model.md) · [security-model.md](../compliance/security-model.md) · [rbac-matrix.md](../compliance/rbac-matrix.md) · [F08](../features/F08-privacy-safety-architecture.md) · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)

> **Status banner — 2026-09-09 ~02:20.** The cases below were written and executed against the `backend/` tree at ~02:00, and 15 of them were RED. **Those findings were acted on: every one is now fixed and carries a regression test** in `backend/tests/test_security_hardening.py` (suite green, `115 passed`). Case headings say **FIXED** where that is so, each such case ends with a `> Closed` note recording what was re-verified by execution, and §2/§3 carry the per-case status. The **[test-plan.md](test-plan.md) §4 gate is GREEN.** Bodies still describe the original finding in the present tense — that is deliberate, it is the evidence the fix was built from — so read the heading and the closing note, not the narration, for current status. Still genuinely open: TC-415, TC-424, TC-432 (accepted), TC-439, TC-459, TC-460.

## 0. What this document is

[test-plan.md](test-plan.md) §4 defines the ADR-0003 firewall gate at the level of intent (TC-401…TC-409). This document expands that intent into **executable** cases with the exact HTTP request, so QA (tejas) can run every one by hand against a running API without reading Python.

Rules:

- **TC-401 … TC-409 are unchanged and not renumbered.** They stay in [test-plan.md](test-plan.md) §4 and remain the must-pass gate. TC-406 was never assigned in test-plan.md and is left reserved-unused rather than recycled.
- New cases run from **TC-410 to TC-460**. Each names the threat it covers ([threat-model.md](threat-model.md) §5) and the automated test file that **should** cover it.
- The automated test files under `backend/tests/` are named as a *specification for the backend owner*. `backend/` is owned by kv; I do not edit it in this task (AGENTS.md rule 2).
- Cases whose expected result is **RED** are known failures found on 2026-09-09. Marking them red here is the point: an untested weakness is worse than a documented one.

## 1. Setup — how tejas runs these by hand

Run once, from `/Users/ns/code/sih-hackathon-26/backend`:

```bash
# 1. seed a throwaway database
rm -f /tmp/saarthi_qa.db
SAARTHI_DATABASE_URL="sqlite:////tmp/saarthi_qa.db" ./.venv/bin/python -m app.seed
# -> "seeded demo data; login jawan.demo / saarthi"

# 2. start the API on 8099
SAARTHI_DATABASE_URL="sqlite:////tmp/saarthi_qa.db" \
  ./.venv/bin/python -m uvicorn app.main:app --port 8099
```

In a second terminal:

```bash
API=http://127.0.0.1:8099
tok () { curl -s -X POST $API/auth/login -H 'Content-Type: application/json' \
          -d "{\"username\":\"$1\",\"password\":\"saarthi\"}" \
        | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])'; }
H ()   { echo "Authorization: Bearer $(tok $1)"; }

# smoke test — must print the health body
curl -s $API/health
```

**Seeded principals** (all password `saarthi`, from `backend/app/seed.py:94-148`):

| Username | Role | Unit | Pseudonym |
|---|---|---|---|
| `jawan.demo` | jawan | 3BN | `ps_demo01` |
| `jawan.tiny` | jawan | TINY | `ps_tiny1` |
| `counsellor.a` | counsellor | — | — |
| `welfare.a` | welfare_officer | 3BN | — |
| `commander.3bn` | commander | 3BN | — |
| `commander.tiny` | commander | TINY | — |
| `admin` | admin | — | — |
| `auditor` | auditor | — | — |
| `hr.ingest` | hr_ingest | — | — |

**Seeded data:** unit `3BN` has 12 people (`ps_demo01`, `ps_3bn02` … `ps_3bn12`); unit `TINY` has 4 (`ps_tiny1` … `ps_tiny4`) — deliberately below k = 5. Persona identity is `CR-DEMO-01` / "Demo Constable".

**Reading the result column:** every case states an exact expected HTTP status. `curl -s -o /dev/null -w "%{http_code}\n" ...` prints just the status; drop `-o /dev/null` to see the body.

---

## Section A — Authentication and token integrity (TC-410 … TC-415)

Covers THR-01, THR-02, THR-03, THR-04. Automated in **`backend/tests/test_security_auth.py`** (new file).

### TC-410 · No credential is not a soft failure

**Given** no `Authorization` header, **when** any protected route is called, **then** the API answers `401` and never `200`, on both the individual plane and the aggregate plane.

| Method | Path | Role | Expect |
|---|---|---|---|
| GET | `/risk/ps_demo01` | anonymous | **401** |
| GET | `/aggregates/unit/3BN` | anonymous | **401** |
| GET | `/app/who-viewed` | anonymous | **401** |
| GET | `/audit/events` | anonymous | **401** |

```bash
for p in /risk/ps_demo01 /aggregates/unit/3BN /app/who-viewed /audit/events; do
  echo -n "$p -> "; curl -s -o /dev/null -w "%{http_code}\n" $API$p; done
```

Result on 2026-09-09: **PASS** (401 on all four).

### TC-411 · A tampered signature is rejected

**Given** a valid counsellor token with its last three characters altered, **when** it is presented, **then** `401 {"detail":"invalid token"}` — the signature check in `backend/app/security.py:50` must not be bypassable by body edits.

```bash
T=$(tok counsellor.a); BAD="${T%???}aaa"
curl -s -o /dev/null -w "%{http_code}\n" $API/risk/ps_demo01 -H "Authorization: Bearer $BAD"   # 401
```

Result: **PASS**.

### TC-412 · An expired token is rejected

**Given** a token whose `exp` is one hour in the past (`security.py:42` sets it 12 h ahead by default, `config.py:18`), **when** it is presented, **then** `401`. Mint it with the dev secret:

```bash
./.venv/bin/python - <<'PY'
import jwt, datetime, requests
s="saarthi-dev-secret-change-me-32b+"
now=datetime.datetime.now(datetime.timezone.utc)
t=jwt.encode({"sub":"usr_counsellor_a","role":"counsellor",
              "exp":int((now-datetime.timedelta(hours=1)).timestamp())}, s, algorithm="HS256")
print(requests.get("http://127.0.0.1:8099/risk/ps_demo01",
      headers={"Authorization":f"Bearer {t}"}).status_code)   # 401
PY
```

Result: **PASS**.

### TC-413 · `alg: none` is rejected

**Given** an unsigned JWT with `alg: none` claiming `role: counsellor`, **when** it is presented, **then** `401` — `decode_token` pins `algorithms=["HS256"]` (`security.py:50`), so the algorithm cannot be downgraded by the attacker.

```bash
./.venv/bin/python - <<'PY'
import jwt, requests
t=jwt.encode({"sub":"usr_cmd_3bn","role":"counsellor"}, key="", algorithm="none")
for p in ["/auth/me","/risk/ps_demo01"]:
    print(p, requests.get("http://127.0.0.1:8099"+p,
          headers={"Authorization":f"Bearer {t}"}).status_code)   # both 401
PY
```

Result: **PASS**.

### TC-414 · A forged `role` claim does not escalate

**Given** a token **correctly signed** with the server secret whose `sub` is the commander user `usr_cmd_3bn` but whose `role` claim says `counsellor`, **when** `/risk/{pseudonym_id}` is called, **then** `403 {"detail":"insufficient role"}` — because `get_current_user` re-reads the `User` row (`security.py:67`) and `require_roles` checks the **database** role (`security.py:75`), never the claim.

```bash
./.venv/bin/python - <<'PY'
import jwt, datetime, requests
s="saarthi-dev-secret-change-me-32b+"; now=datetime.datetime.now(datetime.timezone.utc)
t=jwt.encode({"sub":"usr_cmd_3bn","role":"counsellor","username":"commander.3bn",
              "iat":int(now.timestamp()),
              "exp":int((now+datetime.timedelta(hours=1)).timestamp())}, s, algorithm="HS256")
r=requests.get("http://127.0.0.1:8099/risk/ps_demo01",headers={"Authorization":f"Bearer {t}"})
print(r.status_code, r.text)   # 403 insufficient role
PY
```

Result: **PASS** — this is the single most important negative test in Section A, because it proves the role claim is decorative.

### TC-415 · The deployment does not run on the committed dev secret · **RED (deployment check)**

**Given** a deployed environment, **when** the effective settings are read, **then** `SAARTHI_JWT_SECRET` must be set to a value that is **not** `saarthi-dev-secret-change-me-32b+` (the default literal at `backend/app/config.py:17`).

Manual check (run on the target host, not in CI):

```bash
python3 -c "import os;v=os.environ.get('SAARTHI_JWT_SECRET');\
print('FAIL: default secret in use' if not v or 'change-me' in v else 'PASS: %d chars' % len(v))"
```

Expected: `PASS`. Status on the dev checkout: **RED by design** — the default is in use, which is correct for a local demo and fatal in a pilot. Covers THR-03. This is a runbook item, not a pytest; add it to [demo-runbook.md](demo-runbook.md) pre-flight and the pilot deployment checklist.

---

## Section B — Role escalation (TC-416 … TC-417)

Covers THR-05. Automated in **`backend/tests/test_security_auth.py`**.

### TC-416 · A jawan token reaches nothing but its own data

**Given** a `jawan.demo` token, **when** each privileged route is called, **then** every one answers `403`.

| Method | Path | Role | Expect |
|---|---|---|---|
| GET | `/risk/ps_3bn05` | jawan | **403** |
| GET | `/signals/ps_3bn05` | jawan | **403** |
| GET | `/interventions/queue` | jawan | **403** |
| GET | `/audit/events` | jawan | **403** |
| GET | `/aggregates/unit/3BN` | jawan | **403** |
| POST | `/privacy/unmask` | jawan | **403** |
| POST | `/jobs/expire-raw` | jawan | **403** |

```bash
JH=$(H jawan.demo)
for p in /risk/ps_3bn05 /signals/ps_3bn05 /interventions/queue /audit/events /aggregates/unit/3BN; do
  echo -n "$p -> "; curl -s -o /dev/null -w "%{http_code}\n" $API$p -H "$JH"; done
```

Result: **PASS** (403 on all).

### TC-417 · Admin holds pipelines, not content; auditor holds events, not content

**Given** an `admin` token and an `auditor` token, **when** the matrix below is exercised, **then** each cell matches — this is [rbac-matrix.md](../compliance/rbac-matrix.md) DT-01…DT-07 expressed as HTTP.

| Method | Path | admin | auditor |
|---|---|---|---|
| GET | `/risk/ps_demo01` | **403** | **403** |
| GET | `/signals/ps_demo01` | **403** (explicit deny at `signals.py:46-47`) | **403** |
| GET | `/app/who-viewed` | **403** | **403** |
| GET | `/aggregates/unit/3BN` | **403** | **200** |
| GET | `/audit/events` | **403** | **200** |
| GET | `/audit/verify` | **200** | **200** |
| POST | `/jobs/expire-raw` | **200** | **403** |

```bash
AH=$(H admin); UH=$(H auditor)
for p in /risk/ps_demo01 /signals/ps_demo01 /app/who-viewed /aggregates/unit/3BN /audit/events /audit/verify; do
  printf "%-28s admin=%s auditor=%s\n" $p \
    "$(curl -s -o /dev/null -w '%{http_code}' $API$p -H "$AH")" \
    "$(curl -s -o /dev/null -w '%{http_code}' $API$p -H "$UH")"; done
```

Result: **PASS** on all fourteen cells.

---

## Section C — IDOR on every path parameter (TC-418 … TC-425)

Every path parameter in the API — `{pseudonym_id}`, `{case_id}`, `{unit_id}`, `{request_id}`, `{batch_id}`, `{proposal_id}`, `{run_id}`, `{bundle_id}`, `{dataset}`. Covers THR-06, THR-07, THR-07b, THR-08, THR-08b, THR-09, THR-10, THR-11. Automated in **`backend/tests/test_security_idor.py`** (new file).

**Coverage guard — run this first.** The client-surface routers landed while this suite was being written, so the case list must be provably complete against the live route table:

```bash
curl -s $API/openapi.json | python3 -c "
import sys,json
print('\n'.join(sorted(p for p in json.load(sys.stdin)['paths'] if '{' in p)))"
```

Every path printed must appear in a TC-418…TC-425 case. Make this an assertion in `test_security_idor.py`: **a new route with a path parameter and no IDOR case fails the suite.** Without it, this section silently rots every time a router is added.

### TC-418 · `{pseudonym_id}` on `/risk` — counsellor curiosity browsing · **FIXED 2026-09-09 ~02:20**

**Given** a `counsellor.a` token and a pseudonym the counsellor has **no case for and no consent from**, **when** `GET /risk/{pseudonym_id}` is called, **then** it *should* answer `403` (caseload or active unmask grant required, plus an active consent artefact per [rbac-matrix.md](../compliance/rbac-matrix.md) DT-02) — **today it answers `200` with the full score, tier, confidence and factor list.**

| Method | Path | Role | Expected | Actual 2026-09-09 |
|---|---|---|---|---|
| GET | `/risk/ps_3bn05` | counsellor | 403 | **200** |
| GET | `/risk/ps_tiny1` | counsellor | 403 | **200** |
| GET | `/risk/ps_demo01/explanation` | counsellor | 403 unless assigned | **200** |
| GET | `/risk/ps_3bn05/trend` | counsellor | 403 | **200** |
| GET | `/risk/ps_tiny1/trend` | counsellor | 403 | **200** |

```bash
CH=$(H counsellor.a)
for p in ps_demo01 ps_3bn05 ps_tiny1; do
  echo -n "$p        -> "; curl -s -o /dev/null -w "%{http_code}\n" $API/risk/$p -H "$CH"
  echo -n "$p/trend  -> "; curl -s -o /dev/null -w "%{http_code}\n" $API/risk/$p/trend -H "$CH"; done
```

**The fix already exists one file away.** `_assert_assigned` (`backend/app/api/routers/counsellor.py:72-99`) implements exactly the caseload check these routes need, and `active_consent` (`backend/app/consent.py:13-20`) the consent half — `/privacy/unmask` already calls it (`privacy.py:86`). The three unscoped routes simply do not call either. This is a wiring fix, not a design problem.

**RED.** Covers THR-06 and abuse case AC-4 ([threat-model.md](threat-model.md) §6). The compensating control that *does* work: the read is audited (`risk.py:59-68`) and the subject sees it — verify that half with TC-459. Fix is specified in [threat-model.md](threat-model.md) §6 AC-4.

> **Closed 2026-09-09 ~02:20.** CORS-independent: `authz.assert_subject_scope` now guards the route. **[re-verified]** `counsellor.a` → `/risk/ps_3bn05` = **403**. Regression cover: `backend/tests/test_security_hardening.py::test_tc418_*`.

### TC-419 · `{pseudonym_id}` on `/signals` — same hole, richer data · **FIXED 2026-09-09 ~02:20**

**Given** a `counsellor.a` token, **when** `GET /signals/ps_3bn05` is called, **then** it *should* be `403`; today it returns `200` with the whole signal vector (`days_since_home_leave`, `leave_cancel_count`, duty streak, …) for an unrelated person.

```bash
curl -s $API/signals/ps_3bn05 -H "$CH"    # 200 + full signal dict
```

**RED.** Covers THR-06. Note the *correct* behaviour is already present one role over: admin is explicitly denied at `signals.py:46-47`.

> **Closed 2026-09-09 ~02:20.** `authz.assert_subject_scope` now guards `/signals/{id}`. **[re-verified]** `counsellor.a` → `/signals/ps_3bn05` = **403**. Regression cover: `backend/tests/test_security_hardening.py::test_tc419_*`.

### TC-420 · `{case_id}` on `/interventions` — acting on someone else's case · **FIXED 2026-09-09 ~02:20**

**Given** counsellor A and a case assigned to counsellor B, **when** A posts an action, an outcome, or a Tele-MANAS referral against B's `case_id`, **then** it *should* be `403`; today the handlers fetch by id with `db.get(ResponseCase, case_id)` and no assignee check (`interventions.py:89`, `:128`, `:176`), so A can close B's case and export the outcome label.

| Method | Path | Role | Body | Expected | Actual |
|---|---|---|---|---|---|
| GET | `/interventions/queue` | counsellor | — | 200, **filtered to own caseload** (`interventions.py:59-61`) | **200 filtered — PASS** |
| POST | `/interventions/{case_id}/actions` | counsellor not assigned | `{"catalogue_id":"buddy_nudge"}` | 403 | **200** |
| POST | `/interventions/{case_id}/outcome` | counsellor not assigned | `{"outcome":"declined"}` | 403 | **200** + case closed |
| POST | `/interventions/{case_id}/telemanas` | counsellor not assigned | `{}` | 403 | **200** |

Procedure: read a `case_id` from `GET /interventions/queue` as `welfare.a` (whose scope is wider), then replay the three POSTs as `counsellor.a`. **The queue is filtered but the item routes are not** — the classic "the list is scoped, the detail is not" IDOR. Covers THR-07.

Contrast this with the **newer** case routes, which get it right — the point of the case is that the API now has two generations of case handling and only one is safe:

| Method | Path | Guard | Result |
|---|---|---|---|
| GET | `/interventions/case/{case_id}` | `_assert_assigned` `counsellor.py:72-99` | 403 + `case.deny` audit row for a non-assigned counsellor |
| GET | `/interventions/case/{case_id}/timeline` | same | 403 |
| GET | `/interventions/case/{case_id}/notes` | same | 403 |
| POST | `/interventions/{case_id}/actions` | **none** | **200 for anyone with the counsellor role** |

> **Closed 2026-09-09 ~02:20.** `authz.assert_case_scope` is now called by the older `/interventions/{case_id}/*` routes as well as the newer ones. Regression cover: `backend/tests/test_security_hardening.py::test_tc420_*`.

### TC-420b · `{case_id}` on session notes — the guarded path and its two gaps

**Given** the guarded case routes, **when** each principal is exercised, **then**:

| Method | Path | Role | Expect | Actual |
|---|---|---|---|---|
| GET | `/interventions/case/{case_id}/notes` | assigned counsellor | **200** | 200 |
| GET | `/interventions/case/{case_id}/notes` | commander | **403** (middleware, `/interventions` denied prefix) | 403 |
| GET | `/interventions/case/{case_id}/notes` | auditor | **403** (content-blind, MHCA §23) | 403 |
| POST | `/interventions/case/{case_id}/notes` | welfare_officer | **403** (`require_roles("counsellor")`, `counsellor.py:353`) | 403 |
| GET | `/interventions/case/{case_id}` | counsellor, case assigned to **another** counsellor | **403** + `case.deny` audit row | 403 |
| GET | `/interventions/case/{case_id}` | counsellor, case **unassigned** (`assigned is None`) | should be 403 | **200** — `counsellor.py:77` treats `None` as permitted |
| GET | `/interventions/case/{case_id}` | welfare_officer with **empty** `assigned_units` | should be 403 | **200** — `counsellor.py:88` short-circuits on falsy |

The last two rows are **RED (narrow)** and cover THR-07b. Both are one-token changes: make an unassigned case require an explicit claim step, and treat an empty `assigned_units` as "no units", not "all units". Note also that session notes are excluded from the 90-day TTL by design ([F08](../features/F08-privacy-safety-architecture.md) §4), so `session_note.free_text` is the longest-lived unencrypted clinical text in the system — see TC-460.

### TC-421 · `{unit_id}` on `/aggregates` — cross-unit commander · **PASS**

**Given** a `commander.tiny` token (unit TINY), **when** `GET /aggregates/unit/3BN` is called, **then** `403 {"detail":"commander may only view own unit chain"}` (`privacy.py:63-64`).

The unit guard must hold on **every** aggregate route, not just the first one — five more landed with the commander dashboard:

| Method | Path | commander.tiny (unit TINY) | commander.3bn |
|---|---|---|---|
| GET | `/aggregates/unit/3BN` | **403** | 200 |
| GET | `/aggregates/unit/3BN/morale` | **403** | 200 |
| GET | `/aggregates/unit/3BN/indicators` | **403** | 200 |
| GET | `/aggregates/unit/3BN/forecast` | **403** | 200 |
| GET | `/aggregates/unit/3BN/trend` | **403** | 200 |
| GET | `/aggregates/unit/3BN/pulse` | **403** | 200 |
| GET | `/aggregates/units` | **`["TINY"]` only** | **`["3BN"]` only** |

```bash
TH=$(H commander.tiny); CMD=$(H commander.3bn)
for s in "" /morale /indicators /forecast /trend /pulse; do
  printf "%-14s tiny=%s 3bn=%s\n" "$s" \
    "$(curl -s -o /dev/null -w '%{http_code}' $API/aggregates/unit/3BN$s -H "$TH")" \
    "$(curl -s -o /dev/null -w '%{http_code}' $API/aggregates/unit/3BN$s -H "$CMD")"; done
curl -s $API/aggregates/units -H "$TH" | python3 -c "
import sys,json;print([u['unit_id'] for u in json.load(sys.stdin)['units']])"   # ['TINY']
```

Result: **PASS** on all seven — `_guard_unit` (`commander.py:57-59`) and `_units` (`commander.py:62-67`) hold. `GET /aggregates/units` deserves a note: it looks like the unit-ranking API that abuse case AC-2 is about, and it is not, precisely because `_units` filters it to one unit for a commander.

**Regression note for the backend owner (RED, narrow — THR-08b):** every one of those guards is written `if user.role == "commander" and user.unit_id and ...`. A commander row with a **null** `unit_id` is unscoped across all units. Add the assertion at seed and at login:

```python
def test_tc421_no_commander_without_a_unit(db_session):
    assert not db_session.query(User).filter(
        User.role == "commander", User.unit_id.is_(None)).all()
```

### TC-422 · `{unit_id}` on `/signals/group` and `/aggregates` for non-commander roles

**Given** a `counsellor.a` token, **when** any `{unit_id}` is requested, **then** `200` is returned for every unit — counsellor/welfare/auditor are deliberately unscoped on group surfaces.

| Method | Path | Role | Expect |
|---|---|---|---|
| GET | `/aggregates/unit/TINY` | counsellor | **200** |
| GET | `/signals/group/3BN/exposure` | counsellor | **200** |
| GET | `/signals/group/TINY/exposure` | welfare_officer | **200** |
| GET | `/signals/group/3BN/exposure` | commander | **403** (middleware, `firewall.py:16`) |

Result: **PASS** — accepted risk THR-09, group-level data only. This case exists to make the acceptance explicit so that a future *individual* field added to the group route is caught.

### TC-423 · `{request_id}` on `/privacy/unmask/{id}/identity` — non-keyholder read · **PASS**

**Given** a granted unmask request held by counsellor A + welfare officer A, **when** counsellor **B** calls `GET /privacy/unmask/{request_id}/identity`, **then** `403 {"detail":"not a keyholder on this grant"}` (`privacy.py:206-207`).

Result: **PASS** (verified with a second counsellor account). Covers THR-10.

### TC-424 · `{batch_id}` on the quarantine report — guessable ids · **RED**

**Given** any `hr_ingest`, `admin` or `auditor` token and a **guessed** batch id, **when** `GET /ingest/hr/batches/{batch_id}/quarantine` is called, **then** the raw rejected row payloads are returned (`ingest.py:72-82`). Batch ids are constructed as `csv-{dataset}-{filename}` (`ingest.py:37`), so `csv-leave-leave.csv` is a plausible guess.

```bash
curl -s "$API/ingest/hr/batches/csv-leave-leave.csv/quarantine" -H "$(H auditor)"
```

Expected after fix: quarantine rows readable only by the batch's own ingest principal, or redacted for `auditor` (who is content-blind everywhere else — see TC-444). **RED**, covers THR-11.

### TC-425 · Self-scoped endpoints expose no path parameter at all · **PASS (structural)**

**Given** the route table, **when** the jawan surface is enumerated, **then** no route on it accepts a subject identifier: `/app/who-viewed` (`privacy.py:351`) and `/app/me/trend` (`app_data.py:123`) resolve the subject from `user.pseudonym_id` on the server. There is no IDOR to attempt.

```bash
curl -s $API/openapi.json | python3 -c "
import sys,json
for p in json.load(sys.stdin)['paths']:
    if p.startswith('/app'): print(p)"
```

**Then** the only `/app/...` path with a parameter is `/app/consent/withdraw/{bundle_id}`, and that one is a **scope selector, not a subject selector**. Result: **PASS**. Assert this as a *route-shape* test so a future `/app/{pseudonym_id}/trend` cannot be added quietly: no `/app/` or `/me/` route may take a parameter named `pseudonym_id`, `personnel_id` or `user_id`.

The two remaining parameters, both correctly scoped:

| Method | Path | Scoping | Result |
|---|---|---|---|
| POST | `/app/consent/withdraw/{bundle_id}` | filtered on `principal_pseudonym == user.pseudonym_id` (`self_service.py:175`) plus a bundle allow-list (`:170-171`) | **PASS** — cannot withdraw another person's consent, and an unknown bundle is 404 |
| GET | `/aggregates/simulations/{run_id}` | `_guard_unit(user, row.unit_id)` **after** the fetch (`commander.py:417`) | **PASS** — a commander cannot read another unit's what-if run |

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST $API/app/consent/withdraw/not_a_bundle -H "$JH"   # 404
```

Note on the `{run_id}` shape: the guard runs *after* `db.get`, so a wrong `run_id` for another unit returns 403 while a nonexistent one returns 404 — a small existence oracle over simulation ids. Simulations carry no individual data (`SimulationRun` is unit-keyed by design, `models.py:577-586`), so this is noted, not raised.

---

## Section D — The ADR-0003 command firewall, both layers (TC-426 … TC-430)

Extends TC-401/402/403. Covers THR-13, THR-14, THR-15, THR-16. Automated in **`backend/tests/test_firewall.py`** (existing file — append, do not renumber).

### TC-426 · Middleware layer — rejected before any handler runs

**Given** a `commander.3bn` token, **when** each denied prefix is called (`firewall.py:16-26`), **then** `403` with body `{"detail":"commander identity cannot access individual welfare data (ADR-0003)"}` — the **middleware** message, not a handler message — and a `firewall.deny` row is appended with `resource_type="route"` (`firewall.py:88-97`).

| Method | Path | Role | Expect |
|---|---|---|---|
| GET | `/risk/ps_demo01` | commander | **403** middleware body |
| GET | `/risk/ps_demo01/explanation` | commander | **403** |
| GET | `/signals/ps_demo01` | commander | **403** |
| GET | `/interventions/queue` | commander | **403** |
| GET | `/app/who-viewed` | commander | **403** |
| POST | `/privacy/unmask` | commander | **403** |
| POST | `/privacy/break-glass` | commander | **403** |
| POST | `/ingest/hr/leave` | commander | **403** |

```bash
CMD=$(H commander.3bn)
curl -s $API/risk/ps_demo01 -H "$CMD"
# {"detail":"commander identity cannot access individual welfare data (ADR-0003)"}
```

Verify the audit side as `auditor`: `GET /audit/events` must contain `action: "firewall.deny"` with `denied: true`. Result: **PASS**.

### TC-427 · Handler layer — the firewall holds with the middleware removed

**Given** the middleware is bypassed (call `forbid_commander` directly, or build a `FastAPI` app without `CommanderFirewallMiddleware`), **when** a commander principal reaches a welfare handler, **then** `HTTPException 403` with detail `commander identity cannot access individual welfare data (ADR-0003)` **and** a `firewall.deny` audit row with reason `ADR-0003 commander cannot access individual welfare data` (`firewall.py:52-67`); a counsellor principal passes through returning `None`.

This one cannot be done with curl — it is the belt-and-braces proof and belongs in pytest:

```python
# backend/tests/test_firewall.py
def test_tc427_handler_layer_independent_of_middleware(db_session):
    cmd = db_session.query(User).filter(User.username == "commander.3bn").one()
    with pytest.raises(HTTPException) as e:
        forbid_commander(cmd, db=db_session, resource_type="risk", resource_id="ps_demo01")
    assert e.value.status_code == 403
    row = db_session.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    assert row.action == "firewall.deny" and row.denied is True
    cns = db_session.query(User).filter(User.username == "counsellor.a").one()
    assert forbid_commander(cns, db=db_session, resource_type="risk") is None
```

Result: **PASS** (verified in-process). Covers THR-14. Without this case, deleting one line in `main.py:41` would silently remove half the firewall and every other test would still be green.

### TC-428 · Middleware allow-list gap — only one layer holds on some paths · **FIXED 2026-09-09 ~02:20**

**Given** a `commander.3bn` token, **when** the paths below are called, **then** the middleware lets them through (`path_denied_to_commander` returns `False`, `firewall.py:38-49`) and only `require_roles` stops them.

| Method | Path | Middleware verdict | Final status | Stopped by |
|---|---|---|---|---|
| POST | `/jobs/expire-raw` | **not denied** | 403 | `require_roles("admin")` `privacy.py:398` |
| GET | `/audit/events` | **not denied** | 403 | `require_roles("auditor")` `audit_api.py:25` |
| GET | `/audit/verify` | **not denied** | 403 | `require_roles("auditor","admin")` `audit_api.py:17` |
| GET | `/i18n/en` | not denied | 200 | — (public strings, intended) |
| GET | `/roster/rebalance/{id}` | not denied | 403 on `welfare_weighted` | `interventions.py:257-267` (intended) |

Assert directly on the predicate so the gap is visible without a running server:

```python
assert path_denied_to_commander("/jobs/expire-raw") is False   # today
assert path_denied_to_commander("/audit/events") is False      # today
```

**RED for defence-in-depth**, not for confidentiality — the outcome is still 403. Fix: add `/jobs` to `COMMANDER_DENIED_PREFIXES` (`firewall.py:16-26`). Covers THR-16.

> **Closed 2026-09-09 ~02:20.** `/jobs` is now in the firewall deny list, so two independent layers hold on that path again. Regression cover: `backend/tests/test_security_hardening.py::test_tc428_*`.

### TC-429 · Path-normalisation bypass attempts

**Given** a `commander.3bn` token, **when** each mutated path is requested, **then** none of them returns `200` or any individual data.

| Path | Expect | Actual |
|---|---|---|
| `/risk/ps_demo01` | 403 | 403 |
| `/risk//ps_demo01` | 403 | 403 |
| `/./risk/ps_demo01` | 403 | 403 |
| `/aggregates/../risk/ps_demo01` | 403 | 403 |
| `/risk/ps_demo01/` | 403 | 403 |
| `/risk%2Fps_demo01` | 403 | 403 |
| `/Risk/ps_demo01` | 404 (no route; case-sensitive) | 404 |
| `//risk/ps_demo01` | 404 (no route) | 404 |

```bash
for p in "/risk/ps_demo01" "/risk//ps_demo01" "/./risk/ps_demo01" \
         "/aggregates/../risk/ps_demo01" "/risk/ps_demo01/" "/risk%2Fps_demo01" \
         "/Risk/ps_demo01" "//risk/ps_demo01"; do
  printf "%-34s %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' --path-as-is "$API$p" -H "$CMD")"; done
```

Result: **PASS** — nothing leaks; 404s are "no such route", not a bypass. Covers THR-13.

### TC-430 · Full route scrape with status assertions (hardens TC-403)

**Given** a `commander.3bn` token, **when** every route in `/openapi.json` is called with each of its methods and path parameters substituted with real seeded ids, **then**:

1. no `2xx` response body contains `ps_demo01`, `CR-DEMO-01`, `"Demo Constable"`, or a `"score"` key, **except** on `/aggregates/*` and `/auth/*`;
2. at least one route is denied (proving the scrape actually reached the firewall);
3. `GET /welfare/personnel/CR-DEMO-01` is **403** with an audit row (`privacy.py:405-421`) — the deliberate trap route;
4. **new vs TC-403:** every denial is `403`, never `404` — a `404` would leak route existence and is not an authorization answer.

The existing `test_tc403_commander_scrape_has_no_individual_score` (`backend/tests/test_firewall.py:35-76`) covers 1–3 but `continue`s past any `>= 400`, so a route that fails for the *wrong reason* passes silently. Assertion 4 is the addition. Covers THR-13, THR-15.

---

## Section E — Dual-key unmask (TC-431 … TC-436)

Extends TC-405. Covers THR-20, THR-21, THR-24. Automated in **`backend/tests/test_privacy.py`** (existing — append).

### TC-431 · One principal cannot supply both keys · **PASS**

**Given** counsellor A opens an unmask request, **when** counsellor A also approves it, **then** the request stays `pending` (never `granted`) and `GET .../identity` answers `403 {"detail":"no active unmask grant"}` (`privacy.py:161`, `:204-205`).

```bash
CH=$(H counsellor.a)
RID=$(curl -s -X POST $API/privacy/unmask -H "$CH" -H 'Content-Type: application/json' \
  -d '{"pseudonym_id":"ps_demo01","reason":"session","purpose_string":"case_review"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["request_id"])')
curl -s -X POST $API/privacy/unmask/$RID/approve -H "$CH"     # status stays "pending"
curl -s -o /dev/null -w "%{http_code}\n" $API/privacy/unmask/$RID/identity -H "$CH"   # 403
```

Then complete it properly: approve as `welfare.a` → `status: granted` with an `expires_at`; read identity as `counsellor.a` → `200` with `personnel_id: CR-DEMO-01`. Result: **PASS**.

### TC-432 · Two accounts, one human, defeats dual-key · **RED (accepted, compensated)**

**Given** the same human holds a `counsellor` account **and** a second `welfare_officer` account, **when** they open a request from one and approve from the other, **then** the request is `granted` and the identity is disclosed — because both guards compare `user.id` only (`privacy.py:137-138`, `:162`) and `User.role` is a scalar (`models.py:30`) so nothing links two accounts to one person.

Procedure (needs a fixture account, hence pytest not curl):

```python
db.add(User(id="usr_sock_w", username="sock.welfare", role="welfare_officer",
            password_hash=hash_password("saarthi"), display_name="Counsellor A second account"))
# open as counsellor.a, approve as sock.welfare -> status "granted"
# GET /privacy/unmask/{rid}/identity as counsellor.a -> 200 with legal_name
```

Result on 2026-09-09: **granted, legal name disclosed.** **RED, accepted for v1** — logged as residual risk THR-21 and in [threat-model.md](threat-model.md) §7 item 2. The compensating controls are the audit chain, the subject's who-viewed receipt, and the oversight board. The test exists so the residual is *demonstrated*, not merely asserted; a jury asking "what if one person has two logins?" gets a run, not a shrug.

### TC-433 · A second counsellor cannot be the second key · **PASS**

**Given** counsellor A opened a request, **when** counsellor **B** approves it, **then** `409 {"detail":"counsellor key already set"}` (`privacy.py:151-152`) — two counsellors are not two keys; the second key must be a welfare officer.

Result: **PASS**.

### TC-434 · No unmask without an active consent artefact · **PASS**

**Given** the subject has withdrawn consent (`POST /app/consent/withdraw` as `jawan.demo`), **when** a counsellor opens an unmask request for them, **then** `403 {"detail":"unmask requires an active consent artefact"}` and an `unmask.deny` audit row with reason `no active consent artefact` (`privacy.py:86-97`).

```bash
curl -s -X POST $API/app/consent/withdraw -H "$(H jawan.demo)"     # {"withdrawn":3,"command_visible":false}
curl -s -X POST $API/privacy/unmask -H "$CH" -H 'Content-Type: application/json' \
  -d '{"pseudonym_id":"ps_demo01","reason":"x","purpose_string":"case_review"}'   # 403
```

Result: **PASS**. This is the MHCA §23 / DPDP §6(2) behaviour under test; re-seed before running later cases.

### TC-435 · The purpose string is a closed vocabulary · **PASS**

**Given** a purpose outside `PURPOSE_VOCAB` (`privacy.py:30-36`), **when** an unmask is opened, **then** `400 {"detail":"purpose not in vocabulary"}`. Use `"ACR_review"` as the probe — it is exactly the purpose the architecture exists to refuse.

```bash
curl -s -X POST $API/privacy/unmask -H "$CH" -H 'Content-Type: application/json' \
  -d '{"pseudonym_id":"ps_demo01","reason":"x","purpose_string":"ACR_review"}'   # 400
```

Result: **PASS**.

### TC-436 · An unmask grant is session-scoped and expires

**Given** a granted request whose `expires_at` (`privacy.py:178`, `unmask_session_hours` = 8, `config.py:27`) is moved into the past, **when** `GET /privacy/unmask/{request_id}/identity` is called by a legitimate keyholder, **then** `403 {"detail":"no active unmask grant"}` (`privacy.py:204-205`).

Pytest: grant, then `req.expires_at = now - timedelta(minutes=1)`, then re-read. Result: **PASS** (guard present and correct).

---

## Section F — Break-glass (TC-437 … TC-439)

Extends TC-409's break-glass half. Covers THR-22, THR-23. Automated in **`backend/tests/test_privacy.py`**.

### TC-437 · Break-glass notifies the subject and the welfare officer · **PASS**

**Given** a `counsellor.a` token, **when** `POST /privacy/break-glass` is called, **then** `200` with `notified_subject: true`, `notified_welfare: true`, `oversight_flag: true` and `expires_at` 24 h out (`privacy.py:239-249`); a `Notification` row is created for the subject with `body_key: notify.breakglass.subject` (`privacy.py:251-260`) and one for the welfare officer (`privacy.py:261-272`); and the subject's `GET /app/who-viewed` contains `action: "break_glass.open"` (`privacy.py:363-375`).

```bash
curl -s -X POST $API/privacy/break-glass -H "$CH" -H 'Content-Type: application/json' \
  -d '{"pseudonym_id":"ps_demo01","reason":"imminent harm"}'
curl -s $API/app/who-viewed -H "$(H jawan.demo)"     # entry with action break_glass.open
```

Result: **PASS**. This is the demo's 15-second trust moment — run it in every rehearsal.

### TC-438 · Break-glass is not gated on consent and is not rate-limited · **FIXED 2026-09-09 ~02:20**

**Given** a subject who has withdrawn **all** consent, **when** a counsellor calls `POST /privacy/break-glass` for them, **then** it *should* still succeed (imminent harm is the whole point — MHCA §23(1), DPDP §7 medical emergency) **but** it should be **rate-limited and oversight-queued per counsellor**; today it can be called repeatedly with no cap and returns `legal_name` on every call (`privacy.py:230-295`).

```bash
curl -s -X POST $API/app/consent/withdraw -H "$(H jawan.demo)"
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -w "%{http_code} " -X POST $API/privacy/break-glass -H "$CH" \
    -H 'Content-Type: application/json' -d '{"pseudonym_id":"ps_demo01","reason":"x"}'; done
# 200 200 200 200 200 — five identity disclosures, five notifications, no throttle
```

**RED**, covers THR-22. The design intent is that break-glass is expensive; today it is cheaper than the dual-key path. Fix: cap per counsellor per week, and make the Nth call in a window require welfare-officer countersignature. The notification and oversight flag remain the only real deterrent, and they *do* fire — so this is an abuse-cost problem, not a silent-leak problem.

> **Closed 2026-09-09 ~02:20.** A weekly cap now returns **429** past the limit and requires an explicit `acknowledge_oversight` flag, writing a `break_glass.throttled` audit row. The *absence of a consent precondition* is deliberate and unchanged — that is what break-glass is for. Regression cover: `backend/tests/test_security_hardening.py::test_tc438_*`.

### TC-439 · The 24-hour break-glass window is a review window, not an access window · **RED (documentation defect)**

**Given** a break-glass event with `expires_at` 24 h out, **when** you look for the route that enforces it, **then** there isn't one: the identity is returned **in the POST response itself** (`privacy.py:284-294`). Nothing later re-checks `expires_at`.

Assertion: no route in `/openapi.json` reads `BreakGlassEvent` for authorization. Expected outcome of this case is a **doc fix, not a code fix** — [rbac-matrix.md](../compliance/rbac-matrix.md) §break-glass says "expires in 24 h", which readers will take as an access window. It is an *oversight-review* window. Covers THR-23.

---

## Section G — Audit chain and tamper detection (TC-440 … TC-444)

Extends TC-409's audit half. Covers THR-32, THR-33, THR-34, THR-35, THR-36. Automated in **`backend/tests/test_security_audit.py`** (new file).

### TC-440 · The audit log is append-only at the database · **PASS**

**Given** the application's own DB connection, **when** `UPDATE audit_events` or `DELETE FROM audit_events` is executed, **then** the statement aborts with `audit log is append-only` (triggers at `db.py:51-68`, installed by `init_db` at `db.py:77`).

```bash
sqlite3 /tmp/saarthi_qa.db "UPDATE audit_events SET action='tamper' WHERE id=1;"
# Error: audit log is append-only
sqlite3 /tmp/saarthi_qa.db "DELETE FROM audit_events WHERE id=1;"
# Error: audit log is append-only
```

Result: **PASS**.

### TC-441 · The hash chain detects content tampering · **PASS**

**Given** an attacker with **superuser** DB rights who drops the triggers first, **when** any hashed field (`action`, `resource_type`, `resource_id`, `purpose`, `reason`, `subject_pseudonym_id`, `denied`, `actor_id`, `actor_role`, `payload` — `audit.py:41-52`) is edited, **then** `GET /audit/verify` returns `{"ok": false, "broken_at": <id>}` (`audit.py:90-91`).

```bash
sqlite3 /tmp/saarthi_qa.db "DROP TRIGGER audit_events_no_update; UPDATE audit_events SET reason='x' WHERE id=1;"
curl -s $API/audit/verify -H "$(H auditor)"     # {"ok":false,"broken_at":1}
```

Result: **PASS** — the chain does its job once the triggers are gone. Re-seed afterwards.

### TC-442 · The hash chain does **not** detect timestamp tampering · **FIXED 2026-09-09 ~02:20**

**Given** the same superuser, **when** only the `at` column is rewritten, **then** `GET /audit/verify` *should* report `ok: false` — **today it reports `ok: true`**, because `at` (`models.py:469`) is absent from the hashed body (`audit.py:41-52`) and from `verify_chain`'s recomputation (`audit.py:77-88`).

```bash
sqlite3 /tmp/saarthi_qa.db "DROP TRIGGER IF EXISTS audit_events_no_update;
                            UPDATE audit_events SET at='2020-01-01 00:00:00' WHERE id=1;"
curl -s $API/audit/verify -H "$(H auditor)"     # {"ok":true,...}  <-- should be false
sqlite3 /tmp/saarthi_qa.db "SELECT id, at, action FROM audit_events WHERE id=1;"
```

**RED**, covers THR-34, and it is the highest-value fix in this document relative to effort: add `"at": row.at.isoformat()` to the body dict in **both** `write_audit` (`audit.py:41-52`) and `verify_chain` (`audit.py:77-88`). Until then the who-viewed receipt can be given a false "when", which is exactly the field a jawan is being asked to trust.

> **Closed 2026-09-09 ~02:20.** `at` and `seq` are now inside the hashed body and recomputed by `verify_chain`. **[re-verified]** with both append-only triggers dropped, rewriting `at` returns `{"ok": false, "broken_at": 1, "reason": "entry_modified"}`. Regression cover: `backend/tests/test_security_hardening.py::test_tc442_*`.

### TC-443 · Tail truncation is undetected · **FIXED 2026-09-09 ~02:20**

**Given** the last N audit rows are deleted (triggers dropped), **when** `GET /audit/verify` runs, **then** it *should* fail — today it returns `{"ok": true, "entries": <fewer>}` because `verify_chain` (`audit.py:73-93`) walks forward from GENESIS with no signed head, no external anchor and no expected-count register.

```bash
sqlite3 /tmp/saarthi_qa.db "DROP TRIGGER IF EXISTS audit_events_no_delete;
                            DELETE FROM audit_events WHERE id > (SELECT MAX(id)-3 FROM audit_events);"
curl -s $API/audit/verify -H "$(H auditor)"    # ok:true with a smaller "entries" count
```

**RED**, covers THR-35. Minimal v1 fix: persist a monotonically increasing head counter outside `audit_events`, or ship the head hash off-box (append to a WORM file / print to a second sink) once per hour, and have `/audit/verify` compare.

> **Closed 2026-09-09 ~02:20.** A new `AuditCheckpoint` row stores `entry_count` + `head_hash`, advanced on every write and compared by `verify_chain`. A removed tail now returns `entry_count_mismatch`; a rewritten head returns `head_mismatch`. Still detection, not prevention — the checkpoint shares the DB, so an external anchor remains future scope. Regression cover: `backend/tests/test_security_hardening.py::test_tc443_*`.

### TC-444 · The auditor is content-blind · **PASS**

**Given** an `auditor` token, **when** `GET /audit/events` is called, **then** the response contains `id, at, actor_role, action, resource_type, denied, purpose` and **never** `reason`, `payload` or `subject_pseudonym_id` (`audit_api.py:29-40`).

```bash
curl -s $API/audit/events -H "$(H auditor)" | python3 -c "
import sys,json; ks=set()
for e in json.load(sys.stdin)['events']: ks |= set(e)
print(sorted(ks))
assert not ks & {'reason','payload','subject_pseudonym_id'}, 'CONTENT LEAK'
print('PASS: auditor is content-blind')"
```

Result: **PASS**. This is what makes the audit trustworthy *to the jawan* ([rbac-matrix.md](../compliance/rbac-matrix.md) DT-01/02/08), so assert it on the key set, not on a sample row.

---

## Section H — Consent gate on every voluntary-bundle write (TC-445 … TC-449)

Extends TC-407. Covers THR-25, THR-26, THR-28. Automated in **`backend/tests/test_privacy.py`**.

### TC-445 / TC-446 / TC-447 · Every voluntary write is consent-gated · **PASS**

**Given** `jawan.demo` has withdrawn consent, **when** each voluntary-bundle write endpoint is called, **then** all three answer `403 {"detail":"voluntary bundle requires consent"}` — the gate is `has_voluntary_consent` (`consent.py:23-33`), called at `app_data.py:57-58`, `:81-82`, `:109-110`.

| TC | Method | Path | Body | Before withdrawal | After withdrawal |
|---|---|---|---|---|---|
| TC-445 | POST | `/app/checkins` | `{"mood_label":"ok","mood_score":3,"sleep_hours":6}` | **200** | **403** |
| TC-446 | POST | `/app/instruments` | `{"instrument":"phq9","score":5}` | **200** | **403** |
| TC-447 | POST | `/app/passive` | `{"sleep_hours_proxy":5.0}` | **200** | **403** |

```bash
JH=$(H jawan.demo)
curl -s -o /dev/null -w "%{http_code}\n" -X POST $API/app/checkins -H "$JH" \
  -H 'Content-Type: application/json' -d '{"mood_label":"ok","mood_score":3}'    # 200
curl -s -X POST $API/app/consent/withdraw -H "$JH"
for b in '/app/checkins {"mood_label":"ok"}' '/app/instruments {"instrument":"phq9","score":5}' \
         '/app/passive {"sleep_hours_proxy":5.0}'; do
  set -- $b; echo -n "$1 -> "
  curl -s -o /dev/null -w "%{http_code}\n" -X POST $API$1 -H "$JH" -H 'Content-Type: application/json' -d "$2"; done
```

Result: **PASS** on all three (verified). Coverage note: these are the *only* three voluntary-bundle write endpoints in the API today (`VOLUNTARY_BUNDLES` at `consent.py:10` lists a fourth, `unit_pulse`, whose endpoint does not exist yet — when APP-009 lands, add TC-449a for it).

### TC-448 · Silent withdrawal is invisible on every command surface · **PASS**

**Given** the commander aggregate for 3BN captured before a withdrawal, **when** `jawan.demo` withdraws and the aggregate is fetched again, **then** the two payloads contain no `consent` or `withdraw` substring, `k` is unchanged, and no field changes shape — the commander cannot detect that anyone withdrew.

```bash
CMD=$(H commander.3bn)
curl -s $API/aggregates/unit/3BN -H "$CMD" > /tmp/before.json
curl -s -X POST $API/app/consent/withdraw -H "$(H jawan.demo)"
curl -s $API/aggregates/unit/3BN -H "$CMD" > /tmp/after.json
grep -ci "consent\|withdraw" /tmp/before.json /tmp/after.json    # 0 and 0
diff <(python3 -c "import json;print(sorted(json.load(open('/tmp/before.json'))))") \
     <(python3 -c "import json;print(sorted(json.load(open('/tmp/after.json'))))")   # no diff
```

Result: **PASS**. Structural reason: `aggregate_unit` reads only `identity_map` and `risk_score` (`kanonymity.py:12-23`) — there is no read path from the consent store to any command surface. Watch item: assert on the **key set**, so a future aggregate field derived from data *density* (which would leak withdrawal) fails this case.

### TC-449 · The consent artefact does not prove its own content · **FIXED 2026-09-09 ~02:20**

**Given** a granted consent artefact, **when** `artefact_hash` is inspected, **then** it *should* be a digest over `{bundle_id, purpose_string, data_categories, language, consent_version, granted_at, principal_pseudonym}` — today it is `nid("h")`, a random UUID fragment (`privacy.py:316`, `ids.py:6-7`).

```bash
sqlite3 /tmp/saarthi_qa.db "SELECT consent_id, bundle_id, artefact_hash FROM consent_artefacts LIMIT 3;"
# artefact_hash looks like h_3f9c1a0b7e42 — a random id, not a digest
```

**RED**, covers THR-28. Consequence: under a DPDP §6 challenge ("prove what he agreed to"), the audit row is the only evidence and the artefact adds nothing. Fix is three lines using the `_hash` helper already in `audit.py:17-19`.

---

## Section I — k-anonymity, complement suppression, differencing (TC-450 … TC-452)

Extends TC-402. Covers THR-17, THR-18, THR-19. Automated in **`backend/tests/test_security_kanonymity.py`** (new file).

> **Closed 2026-09-09 ~02:20.** `consent.artefact_hash()` now digests the canonical artefact content (principal, bundle, purpose, categories, language, version, `granted_at`), so a later edit of the purpose or category list is detectable. Regression cover: `backend/tests/test_security_hardening.py::test_tc449_*`.

### TC-450 · A sub-k unit is fully suppressed · **PASS**

**Given** unit `TINY` with 4 people (below k = 5, `config.py:20`), **when** `GET /aggregates/unit/TINY` is called by `commander.tiny`, **then** `n` is `null`, `n_suppressed` is `true`, `elevated_share` is `null`, and no cell exposes a count between 1 and 4 (`kanonymity.py:34-40`, `:64-65`).

```bash
curl -s $API/aggregates/unit/TINY -H "$(H commander.tiny)"
# {"unit_id":"TINY","k":5,"n":null,"n_suppressed":true,...,"elevated_share":null,...}
```

Result: **PASS**.

### TC-450b · Every aggregate surface suppresses below k, including the longitudinal ones

**Given** a `commander.3bn` token, **when** each of the six aggregate surfaces is fetched, **then** every one carries an explicit `suppressed` / `k` contract and no cell, point or index is derived from fewer than 5 contributors.

| Method | Path | Must expose | Actual 2026-09-09 |
|---|---|---|---|
| GET | `/aggregates/unit/3BN` | `k`, `n`, `n_suppressed`, per-cell `suppressed` | present — but see TC-451 |
| GET | `/aggregates/unit/3BN/morale` | `k`, `suppressed`, `reason_key` | `{"k":5,"score":78.3,"suppressed":false,...}` |
| GET | `/aggregates/unit/3BN/indicators` | `k`, `contributor_count`, per-indicator `n` | `{"k":5,"contributor_count":12,...}` |
| GET | `/aggregates/unit/3BN/forecast` | `k`, `suppressed`, `contributor_count` | `{"suppressed":false,"k":5,"contributor_count":12,...}` |
| GET | `/aggregates/unit/3BN/trend` | per-week `n`, `elevated_share`, `suppressed` | `{"points":[{"week_end":"2026-06-16","n":null,"elevated_share":null,"suppressed":true},...]}` |
| GET | `/aggregates/unit/3BN/pulse` | `k`, `contributor_count`, `suppressed` | `{"k":5,"contributor_count":null,"suppressed":true,...}` |

```bash
for s in "" /morale /indicators /forecast /trend /pulse; do
  echo "== $s"; curl -s $API/aggregates/unit/3BN$s -H "$CMD" | head -c 200; echo; done
```

Result: **PASS** on the per-point suppression contract. **Standing residual (THR-19):** `/trend` returns a *series* and `/forecast` an 8-week *projection*. Each point is individually k-safe; a sequence is a richer inference target than a cell, and it is the surface most likely to be read as "the trend under this CO" — i.e. abuse case AC-2 by another route. No query budget and no noise exist (accepted for v1, ADR-0003). Assert per point, and re-run this case whenever a field is added to any aggregate response.

### TC-451 · Differencing attack via `morale_index` recovers a suppressed cell · **FIXED 2026-09-09 ~02:20 — §4 GATE NOW GREEN**

**Given** the seeded unit `3BN` (12 people), **when** a commander fetches the aggregate, **then** no suppressed cell may be recoverable by arithmetic from the other published fields. **Today it is.**

```bash
curl -s $API/aggregates/unit/3BN -H "$(H commander.3bn)"
```

Actual response on the shipped demo fixture, 2026-09-09:

```json
{"unit_id":"3BN","k":5,"n":12,"n_suppressed":false,
 "cells":{"green":{"n":null,"suppressed":true},"amber":{"n":null,"suppressed":true},
          "red":{"n":0,"suppressed":false},"critical":{"n":0,"suppressed":false}},
 "elevated_share":null,"morale_index":0.917,"suppressed_keys":["amber","green"]}
```

The attack, which a commander can do on a phone:

```
green      = round(morale_index × n) = round(0.917 × 12) = 11
amber      = n − green − red − critical = 12 − 11 − 0 − 0 = 1
```

**One person in 3BN is Amber**, recovered from a response that marks that cell `suppressed: true`. Reproduced independently with a 3-amber / 9-green distribution: `morale_index = 0.75`, `n = 12` → `green = 9` → `amber = 3`. Root cause: `morale_index` and `elevated_share` are computed from raw counts (`kanonymity.py:52-59`) without consulting `suppressed_keys`, and `n` is published whenever `n >= k` (`kanonymity.py:64`). `suppressed_keys` additionally names *which* tier is the small one.

**Assertion the automated test must make** — this is the case that turns the finding into a permanent guard:

```python
def test_tc451_no_suppressed_cell_is_recoverable(client):
    d = client.get("/aggregates/unit/3BN", headers=auth_header(client, "commander.3bn")).json()
    if any(c["suppressed"] for c in d["cells"].values()):
        assert d["morale_index"] is None, "morale_index leaks a suppressed cell"
        assert d["elevated_share"] is None, "elevated_share leaks a suppressed cell"
    known = sum(c["n"] for c in d["cells"].values() if not c["suppressed"] and c["n"] is not None)
    hidden = [k for k, c in d["cells"].items() if c["suppressed"]]
    if d["n"] is not None and len(hidden) == 1:
        assert False, "a single suppressed cell is always recoverable as n - known"
    if d["n"] is not None and len(hidden) >= 2:
        assert d["morale_index"] is None and d["elevated_share"] is None
```

**Status when found (~02:00): RED — blocked the [test-plan.md](test-plan.md) §4 gate and therefore the demo** under AGENTS.md rule 9. Fix options given, in order of preference: (a) return `morale_index` / `elevated_share` as `null` whenever any cell is suppressed; (b) also suppress `n`; (c) drop `suppressed_keys` from the commander projection.

**Status now (~02:20): FIXED — §4 gate GREEN.** Options (a) and (c) were both implemented. Re-verified by execution against a freshly seeded fixture, the same request returns:

```json
{"unit_id":"3BN","k":5,"n":12,"n_suppressed":false,
 "cells":{"green":{"n":11,"suppressed":false},"amber":{"n":null,"suppressed":true},
          "red":{"n":0,"suppressed":false},"critical":{"n":null,"suppressed":true}},
 "elevated_share":null,"morale_index":null,"suppressed_cells":2,
 "reason_key":"heat.cell.suppressed"}
```

`morale_index` and `elevated_share` are `null`, so there is no ratio to multiply back up; `suppressed_keys` is gone, replaced by the bare count `suppressed_cells: 2`, so the reader cannot tell which of the two hidden tiers holds the small cell. Regression cover: `backend/tests/test_security_hardening.py::test_tc451_*`.

**Residual, stated plainly.** `n` is still published, so `n − Σ(published cells) = 12 − 11 − 0 = 1` tells a commander that the two suppressed tiers hold **one person between them**. That is the designed limit of complement suppression, not a defect: the disclosure is "one person in this unit is Amber *or* Critical", and which of the two is unknowable from the response. What is now impossible is what TC-451 actually exploited — pinning that person to a *named tier*. Suppressing `n` as well (fix option (b), not taken) would close even this, at the cost of the unit-size denominator the dashboard needs. Tracked as a residual under TC-450b, not as a red case.

### TC-452 · Complement suppression never selects an empty cell · **FIXED 2026-09-09 ~02:20**

**Given** a unit where the only non-suppressed cells have `n = 0`, **when** the aggregate is computed, **then** the complement-suppression loop finds no candidate — `remaining` filters on a **truthy** count (`kanonymity.py:45`), so `0` is excluded. With a single suppressed cell and a published `n`, that cell equals `n − 0 − 0 − 0`.

Reproduce: set 3 of the 12 `3BN` people to `red` and the rest to a tier that leaves the others at zero, then read the aggregate and check whether exactly one cell is suppressed while `n` is published.

**Expected after fix:** if exactly one cell is suppressed, suppress `n` as well (or a second cell regardless of whether its count is zero). **RED**, covers THR-18. Bundle the fix with TC-451.

---

## Section J — Retention and raw-data expiry (TC-453 … TC-455)

Extends TC-408. Covers THR-27, THR-29, THR-30, THR-31. Automated in **`backend/tests/test_security_retention.py`** (new file).

> **Closed 2026-09-09 ~02:20.** `_choose_suppressions` now ranks *all* remaining tiers by `(count, name)`, zero-count cells included. **[re-verified]** unit 3BN suppresses `amber` (1) **and** `critical` (0). Regression cover: `backend/tests/test_security_hardening.py::test_tc452_*`.

### TC-453 · The expiry job is idempotent and preserves the derived trend · **PASS**

**Given** raw check-ins and instrument results older than 90 days (`raw_ttl_days`, `config.py:28`), **when** `POST /jobs/expire-raw` runs twice, **then** the first run purges them, the second purges `0`, and the derived risk trend still resolves.

```bash
AH=$(H admin)
curl -s -X POST $API/jobs/expire-raw -H "$AH"    # {"checkins_purged":N,"instruments_purged":M,"cutoff":"..."}
curl -s -X POST $API/jobs/expire-raw -H "$AH"    # {"checkins_purged":0,"instruments_purged":0,...}
curl -s $API/risk/ps_demo01 -H "$CH" | grep -o '"score":[0-9]*'   # trend survives
```

Result: **PASS** — verified 1+1 then 0+0. Idempotency comes from the `purged` flag filter (`expiry.py:15`, `:21`), and content is nulled in place rather than row-deleted so the trend keeps its shape.

Operational note carried from [dpdp-2023-mapping.md](../compliance/dpdp-2023-mapping.md):99 — there is **no scheduler**; the job runs only when an admin calls it (THR-31). Add it to the demo pre-flight.

### TC-454 · Passive features are never purged · **FIXED 2026-09-09 ~02:20**

**Given** a `PassiveFeature` row older than the TTL, **when** the expiry job runs (twice), **then** it *should* be purged — today it survives with its value intact, because `expiry.py:8` imports only `CheckIn` and `InstrumentResult`.

```bash
sqlite3 /tmp/saarthi_qa.db \
 "INSERT INTO passive_feature (id,pseudonym_id,sleep_hours_proxy,recorded_at)
  VALUES ('pf_qa1','ps_demo01',4.1,'2026-01-01');"
curl -s -X POST $API/jobs/expire-raw -H "$AH" > /dev/null
sqlite3 /tmp/saarthi_qa.db "SELECT id, sleep_hours_proxy, recorded_at FROM passive_feature WHERE id='pf_qa1';"
# pf_qa1|4.1|2026-01-01   <-- should be gone or nulled
```

**RED**, covers THR-30. Passive features are derived, not raw audio (`app_data.py:120` returns `raw_audio: false`), but they are still behavioural data collected under a voluntary bundle (`consent.py:10`) and [F08](../features/F08-privacy-safety-architecture.md) §4 promises the 90-day TTL for that bundle. Either purge them or amend F08's retention table to name the exception — a promise the code does not keep is worse than a narrower promise.

> **Closed 2026-09-09 ~02:20.** `expire_raw` now deletes expired `PassiveFeature` rows and blanks expired `VoiceFeature` rows, reporting `passive_purged` / `voice_purged` counts. Regression cover: `backend/tests/test_security_hardening.py::test_tc454_*`.

### TC-455 · A client-supplied `recorded_at` defeats the TTL · **FIXED 2026-09-09 ~02:20**

**Given** a jawan client that posts a check-in with a **future** `recorded_at`, **when** the expiry job runs at any later date, **then** the row is never purged, because `expires_at` is derived from the client value (`app_data.py:43-48`, `:67`) and the job filters on `recorded_at <= cutoff` (`expiry.py:15`).

```bash
curl -s -X POST $API/app/checkins -H "$JH" -H 'Content-Type: application/json' \
  -d '{"mood_label":"ok","mood_score":3,"sleep_hours":6,"recorded_at":"2099-01-01"}'
sqlite3 /tmp/saarthi_qa.db "SELECT recorded_at, expires_at FROM check_in WHERE recorded_at > '2030-01-01';"
# 2099-01-01|2099-04-01   <-- immortal row
```

**RED**, covers THR-27. Fix: clamp `recorded_at` to `[as_of() - offline_window, as_of()]` on the server, and always derive `expires_at` from the **server** receipt time. The client value stays useful as a *reported* timestamp for offline sync (ADR-0005) but must not drive retention.

---

## Section K — Transport, platform and availability (TC-456 … TC-460)

Covers THR-01, THR-12, THR-37, THR-38, THR-39, THR-42. TC-456…458 automate in **`backend/tests/test_security_auth.py`** / **`test_security_retention.py`**; TC-459 in **`test_privacy.py`**; TC-460 is a manual deployment review.

> **Closed 2026-09-09 ~02:20.** `_day()` now routes the client value through `clock.clamp_capture_date(raw, as_of())`. The client timestamp stays usable as a *reported* offline capture time but can never push `expires_at` outward. Regression cover: `backend/tests/test_security_hardening.py::test_tc455_*`.

### TC-456 · CORS accepts any origin with credentials · **FIXED 2026-09-09 ~02:20**

**Given** a hostile web origin, **when** a preflight is sent for a welfare route, **then** the API *should* refuse it — today it reflects the origin and allows credentials (`main.py:42-48`).

```bash
curl -s -i -X OPTIONS $API/risk/ps_demo01 \
  -H "Origin: https://evil.example" -H "Access-Control-Request-Method: GET" | head -8
```

Actual on 2026-09-09:

```
access-control-allow-credentials: true
access-control-allow-origin: https://evil.example
```

**RED**, covers THR-12. Any page a counsellor visits while logged in can script the console's API surface. Fix: replace `allow_origins=["*"]` with the explicit console origins, or drop `allow_credentials` if the consoles will only ever send an `Authorization` header (bearer tokens are not cookies — with a header-only design, `allow_credentials` is unnecessary and `*` becomes far less dangerous). Expected result after fix: no `access-control-allow-origin` header for `https://evil.example`.

> **Closed 2026-09-09 ~02:20.** CORS origins are now an explicit console allow-list. **[re-verified]** a request carrying `Origin: https://evil.example` comes back with **no** `access-control-allow-origin` header, and the preflight is refused. Regression cover: `backend/tests/test_security_hardening.py::test_tc456_*`.

### TC-457 · Login has no rate limit and no lockout · **FIXED 2026-09-09 ~02:20**

**Given** 200 sequential wrong-password attempts against one account, **when** they are sent, **then** all 200 return `401` at full speed and attempt 201 with the correct password still succeeds — no counter, no backoff, no lockout exists in `authenticate` (`security.py:55-59`) and no rate-limiting middleware exists anywhere in `backend/app/`.

```bash
for i in $(seq 1 200); do
  curl -s -o /dev/null -w "" -X POST $API/auth/login -H 'Content-Type: application/json' \
    -d '{"username":"counsellor.a","password":"wrong"}'; done
curl -s -o /dev/null -w "%{http_code}\n" -X POST $API/auth/login -H 'Content-Type: application/json' \
    -d '{"username":"counsellor.a","password":"saarthi"}'    # 200 — not locked out
```

**RED**, covers THR-01. PBKDF2 at 120k rounds (`passwords.py:7`) makes each attempt cost real CPU, which is a partial mitigation — and simultaneously makes this endpoint the cheapest DoS in the system. Fix: per-username and per-IP throttling with exponential backoff.

> **Closed 2026-09-09 ~02:20.** Repeated failures are now throttled. **[re-verified]** ten consecutive 401s followed by **429**. Regression cover: `backend/tests/test_security_hardening.py::test_tc457_*`.

### TC-458 · Ingest accepts an unbounded upload · **FIXED 2026-09-09 ~02:20**

**Given** an `hr.ingest` token and a large CSV, **when** `POST /ingest/hr/csv` is called, **then** the whole body is read into memory (`ingest.py:35`) with no size cap and no streaming.

```bash
python3 -c "
open('/tmp/big.csv','w').write('pseudonym_id,duty_date,unit_id,shift_code\n' + 'ps_x,2026-01-01,3BN,day\n'*2000000)"
ls -lh /tmp/big.csv
time curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/ingest/hr/csv?dataset=duty_roster" \
  -H "$(H hr.ingest)" -F "file=@/tmp/big.csv"
```

Expected after fix: `413` above a documented cap. **RED**, covers THR-42. Measure and record peak RSS during the run — that number is the DoS budget.

> **Closed 2026-09-09 ~02:20.** The ingest route now enforces a maximum upload size and refuses anything larger. Regression cover: `backend/tests/test_security_hardening.py::test_tc458_*`.

### TC-459 · Who-viewed is complete enough to be a receipt · **RED (coverage)**

**Given** a counsellor performs each auditable read against `ps_demo01`, **when** the subject opens `GET /app/who-viewed`, **then** every one should appear. Today the feed filters to nine whitelisted action names (`privacy.py:363-375`), excludes all denied attempts (`privacy.py:362`) and caps at 100 rows (`privacy.py:379`).

| Action performed by counsellor | Audit action written | Appears in who-viewed? |
|---|---|---|
| `GET /risk/{id}` | `risk.read` | yes |
| `GET /risk/{id}/explanation` | `risk.explanation` | yes |
| `GET /signals/{id}` | `signals.read` | yes |
| `GET /privacy/unmask/{r}/identity` | `identity.read` | yes |
| unmask granted | `unmask.grant` | yes |
| `POST /privacy/break-glass` | `break_glass.open` | yes |
| **failed/denied read attempt** | `*.deny`, `denied=true` | **no** — filtered at `privacy.py:362` |
| **any future read action** | new action name | **no** — not on the whitelist |

```bash
curl -s $API/app/who-viewed -H "$JH" | python3 -c "
import sys,json; print(sorted({e['action'] for e in json.load(sys.stdin)['entries']}))"
```

**RED (coverage, not leak)**, covers THR-37. Two decisions needed from kv as F08 owner: (1) should a *denied* attempt on my record appear in my receipt? — I argue yes, "someone tried and was refused" is exactly the trust-building entry; (2) invert the whitelist into a **deny**-list so a newly added read action is visible by default rather than invisible by default. Also paginate past 100.

### TC-460 · Data at rest is unprotected · **RED (manual, pre-pilot)**

**Given** filesystem or backup access to the deployment, **when** the datastore is opened directly, **then** identity and welfare data *should* be unreadable without a KMS key — today they are plaintext.

```bash
sqlite3 /tmp/saarthi_qa.db "SELECT personnel_id, legal_name, rank, unit_id FROM identity_map LIMIT 3;"
# CR-DEMO-01|Demo Constable|Constable|3BN
sqlite3 /tmp/saarthi_qa.db "SELECT pseudonym_id, mood_label, mood_score, sleep_hours FROM check_in LIMIT 3;"
```

**RED**, covers THR-38 and THR-39. No encryption at rest, no envelope encryption of `identity_map` or raw self-reports, no KMS integration, and no DB grant separation were found in `backend/` as of 2026-09-09, while [security-model.md](../compliance/security-model.md) §Cryptography describes AES-256-GCM envelope encryption. §"Verification status" in that document now records this honestly. Pilot gate: Postgres with per-column encryption for `identity_map.legal_name`, `check_in.*` and `instrument_result.*`, a distinct low-privilege application role, and `REVOKE UPDATE, DELETE ON audit_events` from it.

---

## 2. Summary — case → threat → file → status

| TC | What it proves | Threat | Automated in | Status 2026-09-09 ~02:20 |
|---|---|---|---|---|
| TC-410…414 | JWT integrity: missing, tampered, expired, `alg:none`, forged role | THR-02, THR-04 | `tests/test_security_hardening.py` | PASS |
| TC-415 | No dev secret in a deployment | THR-03 | manual / runbook | RED (dev) |
| TC-416, 417 | Role escalation blocked; admin & auditor content-blind | THR-05 | `tests/test_security_hardening.py` | PASS |
| TC-418, 419 | `{pseudonym_id}` IDOR on `/risk`, `/risk/*/trend`, `/signals` | THR-06 | `tests/test_security_hardening.py` | FIXED — 403 on all three |
| TC-420 | `{case_id}` IDOR on the older `/interventions/{id}/*` routes | THR-07 | `tests/test_security_hardening.py` | FIXED — `assert_case_scope` |
| TC-420b | `{case_id}` on session notes: guard holds; unassigned-case and empty-`assigned_units` gaps | THR-07b, THR-43 | `tests/test_security_hardening.py` | FIXED |
| TC-421, 422 | `{unit_id}` scoping across all 7 aggregate routes; commander-with-no-unit guard | THR-08, THR-08b, THR-09 | `tests/test_security_hardening.py` | FIXED |
| TC-423 | `{request_id}` non-keyholder read | THR-10 | `tests/test_security_hardening.py` | PASS |
| TC-424 | `{batch_id}` guessable quarantine report | THR-11 | `tests/test_security_hardening.py` | RED (open) |
| TC-425 | Self-scoped routes take no subject id; `{bundle_id}` and `{run_id}` scoped | — | `tests/test_security_hardening.py` | PASS |
| TC-426…430 | Firewall at middleware **and** handler, normalisation, scrape | THR-13…16 | `tests/test_firewall.py` | PASS — TC-428 FIXED |
| TC-431, 433, 434, 435, 436 | Dual-key: self-approval, 2×counsellor, consent, purpose, expiry | THR-20, THR-24 | `tests/test_privacy.py` | PASS |
| TC-432 | Two accounts, one human | THR-21 | `tests/test_privacy.py` | RED (accepted) |
| TC-437 | Break-glass notifies subject + welfare | THR-22 | `tests/test_privacy.py` | PASS |
| TC-438, 439 | Break-glass cost and window | THR-22, THR-23 | `tests/test_privacy.py` | TC-438 FIXED; 439 open |
| TC-440, 441, 444 | Append-only, chain detects content edits, auditor blind | THR-32, THR-33, THR-36 | `tests/test_security_hardening.py` | PASS |
| TC-442, 443 | Timestamp tamper, tail truncation | THR-34, THR-35 | `tests/test_security_hardening.py` | FIXED — `at`+`seq` hashed, `AuditCheckpoint` anchor |
| TC-445…448 | Consent gate on all voluntary writes; silent withdrawal | THR-25, THR-26 | `tests/test_privacy.py` | PASS |
| TC-449 | Consent artefact hash is not a digest | THR-28 | `tests/test_privacy.py` | FIXED — real digest |
| TC-450 | Sub-k unit fully suppressed | — | `tests/test_security_hardening.py` | PASS |
| TC-450b | All 6 aggregate surfaces carry a `k`/`suppressed` contract; longitudinal residual | THR-19 | `tests/test_security_hardening.py` | PASS |
| TC-451, 452 | Differencing recovers a suppressed cell | THR-17, THR-18 | `tests/test_security_hardening.py` | FIXED — §4 gate GREEN |
| TC-453 | Expiry idempotent, trend survives | THR-29, THR-31 | `tests/test_security_hardening.py` | PASS |
| TC-454, 455 | Passive not purged; client-set `recorded_at` | THR-30, THR-27 | `tests/test_security_hardening.py` | FIXED — purge + clamp |
| TC-456, 457, 458 | CORS, login throttling, upload cap | THR-12, THR-01, THR-42 | `tests/test_security_hardening.py` | FIXED |
| TC-459 | Who-viewed completeness | THR-37 | `tests/test_privacy.py` | RED (open) |
| TC-460 | Encryption at rest, DB grants | THR-38, THR-39 | manual / pre-pilot | RED (pre-pilot, manual) |

## 3. Red list, ordered by what to fix first

> **Closure note, 2026-09-09 ~02:20.** This list was written at ~02:00 as a work order for the `backend/` owner. **Items 1–9 and 11 have since been implemented and are closed**; each now has a `test_tc<id>_*` regression test in `backend/tests/test_security_hardening.py`, and the whole backend suite is green (`110 passed`). Item 10 (audit head anchoring) was also implemented, via a new `AuditCheckpoint` row. The table is kept as written — it is the spec the fixes were built from — with a **Status** column added. What genuinely remains open is listed under *Still open* below.

Everything below is a finding in *someone else's* file — `backend/` is kv's. These were specified here, not patched by me (AGENTS.md rule 2).

| Order | Fix | Where | Why first | Status |
|---|---|---|---|---|
| 1 | Suppress `morale_index`, `elevated_share` and `suppressed_keys` when any cell is suppressed | `backend/app/privacy/kanonymity.py:52-69` | TC-451 is a **§4 must-pass gate failure on the demo fixture** — a commander recovers `amber = 1` today | **CLOSED** — ratios withheld, `suppressed_keys` removed |
| 2 | Add `at` to the hashed audit body and to `verify_chain` | `backend/app/audit.py:41-52`, `:77-88` | TC-442 — the receipt's "when" is currently forgeable; ~4 lines | **CLOSED** — `at`+`seq` hashed |
| 3 | Call `_assert_assigned` + `active_consent` from `/risk/{id}`, `/risk/{id}/trend` and `/signals/{id}` | `risk.py:49-83`, `counsellor.py:395-403`, `signals.py:39-67` — the helpers already exist at `counsellor.py:72-99` and `consent.py:13-20` | TC-418/419 — abuse case AC-4 has no preventive control; this is wiring, not design | **CLOSED** — 403 verified |
| 4 | Assignee check on the older `/interventions/{case_id}/*` routes | `backend/app/api/routers/interventions.py:81-199` | TC-420 — the newer `/interventions/case/*` routes already do it; two generations, one safe | **CLOSED** — `assert_case_scope` |
| 5 | Lock CORS to the console origins | `backend/app/main.py:42-48` | TC-456 — one-line change, removes a whole attacker class | **CLOSED** — origin not reflected |
| 6 | Server-side clamp on `recorded_at`; purge `PassiveFeature` | `app_data.py:43-48`, `privacy/expiry.py:8-27` | TC-454/455 — DPDP §8(6) promises we do not currently keep | **CLOSED** — `clamp_capture_date`, passive+voice purged |
| 7 | Login throttling; ingest size cap; `/jobs` in the firewall deny list | `security.py:55-59`, `ingest.py:35`, `firewall.py:16-26` | TC-457/458/428 — availability + defence in depth | **CLOSED** — 429 at 10 tries; cap; `/jobs` denied |
| 8 | Real `artefact_hash` digest | `privacy.py:316` | TC-449 — consent evidence quality | **CLOSED** — content digest |
| 9 | Break-glass throttle + oversight escalation | `privacy.py:230-295` | TC-438 — make the emergency path expensive again | **CLOSED** — 429 + oversight ack |
| 10 | Audit head anchoring against tail truncation | `audit.py:73-93` | TC-443 — needs a design decision, not just code | **CLOSED** — `AuditCheckpoint` anchor |
| 11 | Treat an unassigned case and an empty `assigned_units` as "deny", not "allow"; assert no commander has a null `unit_id` | `counsellor.py:77`, `:88`; `commander.py:58`, `privacy.py:63` | TC-420b, TC-421 — two-token changes that close the last scoping gaps | **CLOSED** |

Items 1 and 2 were demo blockers. Items 3–5 were pilot blockers. Items 6–11 were pilot hardening. **All eleven are now closed** (re-verified 2026-09-09 ~02:20).

**Still open**, and deliberately so:

| TC | What | Why it is still open |
|---|---|---|
| TC-415 | Dev JWT secret | Expected locally; a deployment check, enforced by the runbook, not by code |
| TC-424 | Guessable `{batch_id}` quarantine report | HR-ingest surface only; no personal data in the report body |
| TC-432 | One human holding two keyholder accounts | **Accepted risk** — defeating it needs an identity provider, not application code |
| TC-439 | Break-glass window length | Needs a policy decision from the welfare lead, not a code change |
| TC-459 | Who-viewed completeness | Needs the receipt surface to be specified before it can be tested |
| TC-460 | Encryption at rest, DB grants | Pre-pilot infrastructure; manual verification against the deployment target |

**Note on drift.** The client-surface routers (`self_service.py`, `counsellor.py`, `commander.py`, `pulse.py`, `buddy.py`) landed while this suite was being written and are covered above; line numbers are a 2026-09-09 snapshot. The route-inventory guard in Section C is what keeps this suite honest as more land — run it first, every time.
