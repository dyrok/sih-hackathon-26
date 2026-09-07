# Design — Risk Rules Engine (F04)

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05
> Implements [F04](../../features/F04-risk-rules-engine.md) · Stack per [ADR-0006](../decisions/0006-tech-stack.md): pure-Python rules v1; scikit-learn/lightgbm + SHAP reserved for v2 · Related: [design-hr-signal-engine.md](design-hr-signal-engine.md) (input side)

## 1. Module breakdown (`backend/app/risk/`)

```
backend/app/risk/
  sources.py        # adapters: signal_snapshot (F01), self-report (F02), passive (F03)
  baseline.py       # per-person rolling baselines + change-point detection
  ruleset.py        # YAML loader/validator, version pinning, fail-closed activation
  evaluator.py      # rule evaluation → factors (pure)
  aggregator.py     # weighted sum, domain caps, tier bands, hysteresis
  masking.py        # discrepancy-detection overlay
  explainer.py      # top-3 factors + i18n display strings
  scorer.py         # orchestration + persistence (risk_score, risk_factor)
api/routers/risk.py
config/rulesets/v1.yaml
```

Same purity rule as F01: `evaluator`/`baseline`/`aggregator`/`masking` are pure functions of `(signals, history, config, as_of)`; I/O lives only in `sources.py` and `scorer.py`.

## 2. Evaluation pipeline

1. **Gather** — latest `signal_snapshot` + instrument results + passive feature vectors; record `sources_present`.
2. **Baseline** — per signal with sufficient history: trailing mean + deviation; change-point marker on sustained shifts.
3. **Evaluate** — each YAML rule: inputs → condition → factor (weight, observed value, i18n display key).
4. **Aggregate** — per-domain sums with caps → score 0–100.
5. **Tier map + hysteresis** — bands per ruleset; downgrade requires confirmation run.
6. **Masking overlay** — discrepancy conditions → flag + tier floor.
7. **Persist** — append-only score + factors; emit case event to F05 on Amber+.
8. **Audit** — append-only write (NFR-08).

## 3. Ruleset format (`config/rulesets/v1.yaml`)

```yaml
version: 1
tiers: {green: [0, 39], amber: [40, 59], red: [60, 79], critical: [80, 100]}
domains:
  duty:   {weight: 25, cap: 18}
  leave:  {weight: 18, cap: 14}
  deploy: {weight: 15, cap: 12}
  career: {weight: 10, cap: 8}
  health: {weight: 12, cap: 10}
  psych:  {weight: 20, cap: 16}   # self-report + passive
freshness: {max_age_days: 7}
hysteresis: {downgrade_confirmations: 2}
rules:
  - id: R-DUT-01
    domain: duty
    weight: 12
    inputs: [consecutive_duty_days]
    condition: "consecutive_duty_days >= 60"      # demo cfg — clinical review pending
    explain: {key: "risk.factor.duty_streak"}     # i18n en/hi, values interpolated
masking:
  tier_floor: red
  conditions: [validity_fail, straight_lining, too_fast, all_max]
```

- Every rule carries id, domain, weight, i18n explain key — **no hard-coded user-facing strings in code** (AGENTS rule 7).
- Invalid YAML → refuse to load; last good version stays active (fail-closed — scoring never runs on unvalidated config).
- All demo-default thresholds must appear in the traceability table of [model-explainer.md](../../explanation/model-explainer.md) before pilot.

## 4. Baselines & change-point detection

- Baseline per `(pseudonym_id, signal_key)`: trailing cfg window (default 60 days) mean + deviation. Rule conditions may reference `dev_from_baseline` (e.g., sleep −30% vs own baseline — the FR-06 example) or an absolute floor.
- **Change point:** a sustained mean shift marks `change_point_at` and restarts the baseline window — prevents a "new normal" from masking a slow decline. v1 uses a lightweight CUSUM-style drift detector in stdlib code; `ruptures` stays an optional flag, behind the same interface.
- **Cold start** (< cfg history days): absolute-threshold mode only, resulting flags carry `confidence: low`.

## 5. Masking module

- **Inputs:** validity-item results + response patterns (straight-lining, too-fast completion, all-max) from F02 instrument metadata; adverse objective signals; self-report tone.
- **Output:** `masking_flag` with matched condition ids + tier floor (Red).
- **Hard guard:** if voluntary sources are null because of consent withdrawal (FR-17), masking evaluates false — **null ≠ "fine"**; withdrawal must never manufacture a discrepancy.

## 6. Caching & recompute strategy

- **Triggers:** F01 recompute events (dirty pseudonyms ∪ exposed units), F02 sync events (per person), group exposure events, ruleset activation, daily sweep.
- Recompute is cheap and idempotent; scores are **append-only** stamped with `engine_version` + `ruleset_version`, so trend queries filter to one version pair.
- No in-memory cache across processes — Postgres tables are the state; one process recomputes a battalion comfortably inside the NFR-06 60 s budget (single-pass, no parallelism needed at 1,000 personnel).
- Recompute event handling is at-least-once; duplicate events produce identical append-only rows, harmless by construction.

## 7. Testability hooks

- **Golden scenario:** the scripted 90-day demo persona (Green → Amber → Red, masking example) as an end-to-end fixture — ADR-0001's validation requirement.
- **Ruleset mutation tests:** perturb one rule → assert the expected score delta (catches dead rules and silent config drift).
- **Property tests:** score ∈ [0, 100]; deterministic for identical inputs + version; domain caps hold; no factor without a resolvable i18n key.
- **Firewall test:** commander identity → 403 on every `/risk/*` route (ADR-0003 route-level guarantee).
- **Masking-guard test:** consent withdrawal → no mask flag, no tier inflation.
- **Freshness tests:** stale-only inputs → no new score, prior score marked stale in queue view.

## 8. Failure modes

| Failure | Behavior |
|---|---|
| A source missing | degraded mode: score from present sources; `confidence` lowered; `sources_present` recorded |
| All sources stale | no new score written; last score flagged stale — never a silent zero |
| Baseline insufficient | cold-start absolute mode (§4) |
| Ruleset YAML invalid | fail-closed: last good version active, admin alerted |
| Recompute race | job-table single-writer per pseudonym; append-only writes make retries harmless |
| Group event flood | group flag processed once per unit; individual recompute batched |
| Consent withdrawal mid-window | voluntary sources → null; HR-only recompute; masking suppressed |
| Passive contract change (F03) | unknown feature keys ignored + logged, never crash the scorer |

## 9. Open questions

- Change-point detector for v1: hand-rolled CUSUM vs `ruptures` — decide at implementation start, keep behind an interface.
- Passive feature-vector schema — finalise the contract with neel (F03) before passive rules activate.
- `confidence` display semantics in the counsellor console — agree with neel (F06) so evidence cards read honestly.
