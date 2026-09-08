# ML v2 data-collection plan from counsellor labels (ML-004)

> Owner: kv · Status: [x] current · Last updated: 2026-09-08
> Traces: [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [F05](../features/F05-intervention-engine.md) `intervention_outcome` · [model-explainer.md](model-explainer.md) §5

## 1. Principle

v2 trains **only** on counsellor session outcomes. Labels are outcomes of care, not guesses, and humans stay in the loop by construction. Until the label count is defensible, **rules stay the product**. The harness (`python -m app.ml.harness`) reports `v2_readiness.labels` and will not claim a model is ready.

Defensible bar (reasoned, not a statistic): **≥ 200 exported outcome rows** across ≥ 2 units, with rank mix, before any offline training run. Serving a model additionally requires a filled [fairness-audit-checklist.md](fairness-audit-checklist.md).

## 2. Label schema (already emitted by F05)

Each `POST /interventions/{case_id}/outcome` writes:

| Field | Values | Use |
|---|---|---|
| `pseudonym_id` | surrogate | join key — never `personnel_id` |
| `outcome` | improved / unchanged / worsened / declined / no_contact | **primary label** |
| `tier_at_open` | green/amber/red/critical | baseline |
| `recorded_at` | timestamp | survival time origin = case.opened_at |
| `action_id` / `catalogue_id` | INT-* | treatment indicator |
| `label_exported` | bool | training-set flag |

**Do not label from:** self-report alone, commander opinion, ACR, or "the score went down" without a counsellor-entered outcome. Declining an intervention is a label (`declined`), never a risk-raising event (F05).

## 3. Survival framing (the honest question)

The target is **time to burnout-event**, not "stressed today" (Cox 1972).

- Event: counsellor-recorded `worsened` **or** a new Critical case within 90 days.
- Censoring: transfer, resignation, `no_contact`, end of observation. Right-censoring is native — that is why survival analysis is the shape ([model-explainer.md](model-explainer.md) §5.3).
- Features: the F01 snapshot at case open + F04 factors (tabular). Roster/leave series kept as lagged aggregates first; a temporal model only if it beats gradient boosting on those.

## 4. Collection protocol

1. Counsellor console (F06, neel) is the only write path for outcomes. Backend already exports the row (`label_exported=true`).
2. Weekly job (kv, post-pilot): dump exported rows to an on-prem parquet, **pseudonymized**, no identity-map join.
3. DPO review before any training set leaves the welfare cell. No foreign SaaS (ADR-0006).
4. Dual-key is irrelevant here — training never sees names.
5. Consent withdrawal: drop that person's **voluntary** features; HR features may remain on §7(i) legitimate use. Document the missingness; do not impute "fine".

## 5. Model choice (pre-decided, not fashionable)

| Data shape | Model | Explainability |
|---|---|---|
| Tabular HR + instrument scores | LightGBM / XGBoost | SHAP mandatory ([shap-report-template.md](shap-report-template.md)) |
| Time-to-event | Cox / GB survival | same SHAP sentence shape as v1 factors |
| Roster sequences | only if it beats lagged GBT | else drop |

## 6. What would stop v2

- Labels < 200, or all from one unit.
- Fairness checklist stop-ship (rank/unit recall gap unexplained).
- Any path that would require a commander-visible individual score to "evaluate" the model. Evaluation is counsellor-side, on labelled cases.

## Links

[F04](../features/F04-risk-rules-engine.md) · [F05](../features/F05-intervention-engine.md) · [backend/app/ml/harness.py](../../backend/app/ml/harness.py)
