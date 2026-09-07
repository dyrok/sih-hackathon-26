# F04 — Risk Rules Engine

> Owner: kv · Status: [~] drafting · Last updated: 2026-09-05
> Maps to: FR-05, FR-06, FR-07 in [prd.md](../product/prd.md) · [Architecture](../architecture/architecture.md)

## Purpose

Turns triangulated signals into one explainable **0–100 risk score + care tier** per person, scored against the person's **own baseline**. v1 is a **rules engine: clinically grounded, not learned** ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)). Day one there is **zero labelled data** on Indian CAPF personnel stress — we own that openly instead of fabricating accuracy claims.

Core design stance: **under-reporting is the norm** in a high-stigma force. The engine is designed for it, not surprised by it.

## Behavior (pipeline / logic, step by step)

1. **Triangulate three sources — read together, never self-report alone:**
   - HR signals (F01 `signal_snapshot`) — the zero-effort floor;
   - self-report (F02: 10s check-in, PHQ-9 / GAD-7 / PSS-10 / ISI, validity-scale items);
   - passive (F03: on-device voice-prosody feature vectors).
2. **Baseline** — per-person trailing window per signal; **change-point detection** marks sustained shifts. Deviation-from-own-baseline is the primary factor; absolute thresholds are floors only — absolute numbers fail across age, rank, role.
3. **Evaluate** declarative rules (versioned YAML) → factors with observed values.
4. **Aggregate** weighted with per-domain caps (correlated signals must not stack).
5. **Map to tier** Green / Amber / Red / Critical (FR-09 ladder).
6. **Masking overlay** — discrepancy detection can raise the tier (FR-07).
7. **Persist** append-only score + factors + explanation; emit case event to F05 on Amber+.
8. **Hysteresis** — tier downgrade requires confirmation on the next evaluation (no flapping).

Engineering detail: [design-risk-engine.md](../architecture/design/design-risk-engine.md).

## Scoring rules (factor weights, thresholds, baselines, masking flag)

`score = Σ_domain min(domain_cap, Σ triggered factor weights)`, clamped 0–100. Full ruleset lives in versioned YAML (`config/rulesets/v1.yaml`); the table shows representative rules. **All numeric defaults below are demo config values pending clinical review** — no threshold is presented as a validated statistic (AGENTS rule 6).

| Rule | Condition (cfg = config default) | Weight | Explanation string (FR-06, i18n `risk.factor.*`) |
|---|---|---|---|
| R-DUT-01 | consecutive_duty_days ≥ cfg 60 | 12 | "47 consecutive duty days" style — actual value interpolated |
| R-DUT-02 | circadian_disruption_score ≥ cfg 0.6 | 8 | "night-heavy rotating roster" |
| R-LVE-01 | days_since_home_leave ≥ cfg 180 | 8 | "no home leave in 6 months" |
| R-LVE-02 | leave_cancel_count ≥ 2 | 6 | "2 leaves applied, then cancelled" |
| R-LVE-03 | early_return_days ≥ cfg | 4 | "returned early from leave" |
| R-DEP-01 | family_separation_index ≥ cfg | 8 | "X months away from family" |
| R-CAR-01 | inquiry_court_pending = true | 5 | "pending inquiry/court case" |
| R-HEA-01 | sleep proxy −30% vs own 60-day baseline (dev_from_baseline) | 10 | "sleep −30% from your own normal" |
| R-PSY-01 | PHQ-9 in moderate band or above (bands per [clinical-instruments.md](../explanation/clinical-instruments.md)) | 15 | "elevated PHQ-9" |
| R-GRP-01 | unit_incident_exposure (FR-08) | routes to **group case** in F05, not individual weight stacking |
| R-MAS-01 | masking flag (below) | +10 and tier floor Red | "self-report contradicted by duty/leave record" |

**Tier bands** (config): 0–39 Green · 40–59 Amber · 60–79 Red · 80–100 Critical. Critical also fires directly on crisis indicators (e.g., PHQ-9 item 9) or a Critical group event, regardless of score.

**Baselines:** primary mechanism is `dev_from_baseline` — deviation from the person's own trailing window (FR-06 example uses −30% sleep). Change-point detection resets the baseline window after a sustained shift, so a "new normal" cannot mask a slow decline. Cold start (< cfg days of history): absolute thresholds only, flag confidence = low.

**Masking flag (FR-07) — the discrepancy is the feature:**
- Inputs: validity items failing (social-desirability catch items, MMPI lie-scale style) and/or response-pattern anomalies (straight-lining, too-fast completion, all-max answers), **plus** low self-report while objective signals are adverse.
- Canonical case: **"I am fine" + 4h sleep + 60 duty days + 2 cancelled leaves → masking flag.**
- Effect: contributes weight **and floors the tier at Red**. Hiding distress in a high-stigma org is *higher risk*, not a data-quality problem — the faking is the finding.
- Register: labelled a *discrepancy* in the console, never "malingering" (welfare copy rules, [design.md](../architecture/design/design.md) §8).

**FP/FN economics, stated out loud (NFR-07):** a false positive costs one unnecessary cup of tea with a counsellor; a false negative costs a life. Thresholds are biased toward sensitivity; the alert caps in F05 absorb the FP load. Every threshold-tuning PR must state its FP/FN tradeoff in the description.

**v2 path (ADR-0001):** ML trains only on counsellor outcome labels (F05/F06). Model choice by data shape: tabular HR features → gradient-boosted trees; roster/leave time series → temporal model; outcome framing → **survival analysis** (time to burnout event). **SHAP explanations become mandatory**; fairness audit (rank, region, gender, caste/religion proxies) required before any rollout — details in [model-explainer.md](../explanation/model-explainer.md).

## Data model

| Table | Key fields |
|---|---|
| `risk_score` | id, pseudonym_id, score (0–100), tier, confidence, engine_version, ruleset_version, computed_at, sources_present (hr/self/passive) |
| `risk_factor` | score_id, rule_id, domain, weight, observed_value, display_key (i18n), display_value |
| `person_baseline` | pseudonym_id, signal_key, window_days, baseline_mean, deviation, change_point_at, history_days |
| `masking_flag` | score_id, matched_conditions[], tier_floor |
| `group_exposure_link` | score_id, incident_id (FR-08 join) |
| `ruleset` | version, yaml_hash, approved_by, activated_at — append-only; scores reference their version |

## API surface (role-scoped)

| Endpoint | Method | Role | Notes |
|---|---|---|---|
| `/risk/recompute` | POST | internal / cron | body: pseudonym set, or `{"full": true}` |
| `/risk/{pseudonym_id}` | GET | counsellor (pseudonymized), welfare officer (assigned cases) | score + tier + factors |
| `/risk/{pseudonym_id}/explanation` | GET | counsellor, welfare officer | top-3 factors with values |

Commander aggregation is **not served here** — F07 consumes the aggregate service (k ≥ 5, F08). Every `/risk/*` route returns 403 to a commander identity; that rejection is itself audited.

Response sketch (`GET /risk/{pseudonym_id}/explanation`):

```json
{"pseudonym_id": "ps-4f2a", "score": 68, "tier": "red", "confidence": "high",
 "top_factors": [
   {"key": "risk.factor.duty_streak", "value": 47},
   {"key": "risk.factor.sleep_deviation", "value": "-30%"},
   {"key": "risk.factor.leave_cancellations", "value": 2}],
 "masking": false, "engine_version": "v1.2", "ruleset_version": 1}
```

## Edge cases

- **Missing sources** → degraded mode: HR-only still scores (the zero-effort floor); `sources_present` + confidence record what was available. Passive missing ≠ distress.
- **Silent consent withdrawal (FR-17)** → voluntary sources become null, score recomputes HR-only, masking suppressed; withdrawal itself must never raise the score — null ≠ "fine".
- **New joiner** → cold-start absolute mode, confidence low, no invented baseline.
- **Stale data** → signals older than the freshness window contribute zero weight and raise a data-freshness note; the engine never scores silently on old data.
- **Correlated signals** → per-domain caps prevent triple-counting the same duty stress.
- **Group flag + individual score** → FR-08 exposure creates one group case (F05); individuals still scored on own signals, exposure contributes once.
- **Oscillation** → hysteresis: downgrade requires confirmed re-evaluation.
- **Ruleset change mid-history** → scores are append-only with `ruleset_version`; trends compare like-for-like versions.

## Privacy notes (what this must never do)

- Scores and factors are keyed by pseudonym only; identity resolution is F08 dual-key, logged, subject-visible.
- **No route serves individual scores to commander** — architectural firewall (ADR-0003), enforced at route level with an automated test.
- Masking is welfare evidence — never a disciplinary label, never near ACR data.
- The engine never writes to command-visible surfaces; its only outputs are the counsellor/welfare query paths and F05 events.
- Every score read/write lands in the append-only audit log (NFR-08).

## Out of scope / non-goals

- ML scoring in v1; no accuracy claims without labels (ADR-0001).
- **Diagnosis** — instruments carry the standing disclaimer "reflection support, not diagnosis" (design.md §8).
- Executing interventions → F05 consumes; the engine proposes, humans act.
- Commander dashboards / aggregation → F07 + F08.
- Wearable-signal rules → after F03 lands its feature contract.

## Definition of done

- FR-05: 0–100 score from triangulated sources; per-person baselines with change-point detection implemented.
- FR-06: every flag returns top-3 factors with observed values (explanation test passes for all demo cases).
- FR-07: the scripted discrepancy ("fine" + 4h sleep + 60 duty days + 2 cancelled leaves) yields a masking flag with Red floor.
- Demo persona reproduces the scripted 90-day Green → Amber → Red escalation exactly (ADR-0001 validation, test-plan).
- 1,000-person recompute < 60 s (NFR-06).
- Route-level test: commander role → 403 on all `/risk/*` routes.
- Ruleset in versioned YAML; every default threshold traced to PRD/clinical reference or explicitly marked demo-cfg.

## Links

- [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) rules-not-ML · [ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md) firewall
- Engineering design: [design-risk-engine.md](../architecture/design/design-risk-engine.md)
- Explanation: [model-explainer.md](../explanation/model-explainer.md) (v2 models, SHAP, fairness) · [clinical-instruments.md](../explanation/clinical-instruments.md) (instrument bands)
- Related: [F01](F01-hr-signal-engine.md) (inputs) · [F02](F02-jawan-app.md) (self-report + validity items) · [F03](F03-on-device-signals.md) (passive) · [F05](F05-intervention-engine.md) (consumer) · [F08](F08-privacy-safety-architecture.md) (pseudonyms, audit)
