# ADR-0001 — Rules engine v1, ML v2 from counsellor labels

> Owner: kv · Status: accepted (2026-09-05) · Format: MADR v4 (lean)

## Decision
Ship v1 as a **clinically grounded, transparent rules engine**. Train ML v2 only once counsellor session outcomes accumulate as labels (human-in-the-loop). Frame the whole thing as **survival analysis** ("time to burnout event"), with per-person baselines via change-point detection.

## Context
Day one there is zero labelled data on Indian CAPF personnel stress. Judges (and ethics) require explainability: every alert must list its reasons. "AI" claims without validation are an SIH red flag.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **Rules engine v1 (chosen)** | Explainable by construction; no labelled data needed; clinically defensible; trivially auditable | Hand-tuned thresholds; needs domain grounding |
| ML from day one | Feels impressive | No labels → fabricated accuracy claims; unexplainable; judges attack it |
| Hybrid day one | — | Still no labels; added complexity for a 36h build |

## Consequences
- v1 thresholds documented with clinical citations in [model-explainer.md](../../explanation/model-explainer.md).
- v2 model choices are pre-decided by data shape: tabular HR features → gradient-boosted trees; roster/leave time series → temporal model; outcome framing → survival analysis. SHAP explanations become mandatory at that point.
- Fairness audit required before any v2 rollout (rank, region, gender, proxy variables).
- Threshold tuning states the FP/FN economics out loud: false positive = unnecessary cup of tea with a counsellor; false negative = a life.

## Validation
Rules engine passes [test-plan.md](../../quality/test-plan.md) cases; demo persona reproduces the scripted 90-day escalation exactly.

## Links
[four/0003](0003-two-tier-output-k-anonymity.md) (who sees what) · [model-explainer.md](../../explanation/model-explainer.md) · [F04](../../features/F04-risk-rules-engine.md)
