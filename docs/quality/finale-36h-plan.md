# Finale 36h execution plan + 3-min demo script (PM-005)

> Owner: kv · Status: [x] current · Last updated: 2026-09-08
> Grand Finale: offline nodal centre, December 2026 (SIH 2026 Guidelines). Only the 6 registered students + up to 2 mentors on venue.
> The 3-minute script lives in [demo-runbook.md](demo-runbook.md) §1 and is **not duplicated** here — this file is the hour plan.

## Doctrine (from winner accounts + our ADRs)

Architecture is **already decided** (this repo). Hour 0 we do not argue stack. We start from `main`, seed the demo database, and cut features that are not in the 3-minute loop.

## Hour plan

| Hours | Clock | Who | Work | Done when |
|---|---|---|---|---|
| 0–1 | start | kv + neel | clone, `python -m app.seed`, `pytest -q`, `uvicorn` up, two devices on local network | `/health` 200, persona scores |
| 1–4 | | neel | wire app + consoles to the live API; Hindi check-in; who-viewed screen | 10-second check-in round-trips |
| 1–4 | | kv | freeze ruleset; no threshold thrash; firewall tests on the venue machine | `test_firewall.py` green |
| 4–8 | | risa + tejas | restage deck on venue projector; record a **new** fallback video from the venue build | mp4 on two devices |
| 4–8 | | ayush + manan | citation/statute pack printed; no new claims | cheat sheet in hand |
| 8–12 | | neel + kv | one real bug pass (offline queue, k-anonymity cell, dual-key) | demo loop twice without crash |
| 12–16 | sleep rotation | 3 up / 3 down | — | — |
| 16–20 | | kv | mentor-feedback rows from any mid-finale jury walk-by → [mentor-feedback.md](../../executable/mentor-feedback.md) | rows closed or waived |
| 20–24 | | whole team | 3× full 3-minute rehearsal on the venue projector (runbook §5 rows 3–5) | timing ≤ 3:00 |
| 24–28 | | neel | UI polish only (contrast, Hindi wrap, no new screens) | no feature adds |
| 28–32 | | kv + risa | Q&A drill from runbook §6; one person assigned to write follow-ups | no arguing with jury |
| 32–36 | | tejas | bag owner: laptop + hotspot + pen drive + PDF + mp4; airplane-mode smoke | checklist ticked |

## What we will not start in 36h

- ML v2 training (no labels — ADR-0001).
- Tele-MANAS network API (v1 records the handoff only).
- New signal families, facial analysis, phone monitoring.
- Any commander individual-score "just for the demo". That is a disqualification, not a shortcut.

## 3-minute script

Use [demo-runbook.md](demo-runbook.md) §1 verbatim. Presenter order: problem (kv, 10 s) → live loop (neel, 90 s) → impact (kv, 20 s) → architecture (kv, 20 s) → scale (risa, 10 s). Who-viewed is the 15-second pause — do not rush it.

## Roles on the floor

| Member | Floor job | Never |
|---|---|---|
| kv | demo driver + architecture answers | merge unreviewed hotfixes onto the demo branch without neel |
| neel | app/console driver | invent a statistic |
| risa | deck + timing | skip the fallback copy |
| tejas | bag + recording | leave the pen drive on one device |
| ayush | citations | quote an unverified number |
| manan | DPDP/MHA one-liners | give legal advice beyond the mapping docs |
