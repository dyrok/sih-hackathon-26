# Fairness audit checklist + SHAP report template (ML-003)

> Owner: kv · Status: [x] current · Last updated: 2026-09-08
> Traces: [ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md) · [model-explainer.md](model-explainer.md) §5.5 · NFR-05 / NFR-07
> v1 ships a **rules engine**. This checklist is mandatory **before any ML v2 rollout**. It is also the audit we run on the v1 rules themselves (alert-rate stratification), so we do not wait for labels to start measuring.

## 1. Why this exists

A model (or a ruleset) that flags certain ranks, regions, genders, or caste/religion **proxies** more often is a fairness failure even if it "predicts" well. Flagged-and-stigmatised personnel are the harm, not a rounding error. The architectural firewall ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)) stops scores reaching command; it does **not** stop a biased engine from flooding one community's counsellor queue.

## 2. Protected attributes and proxies (do not collect what we do not need)

| Attribute | Direct field in SAARTHI v1? | Proxy risk in HR signals |
|---|---|---|
| Rank | yes (`identity_map.rank`) | duty load, night ratio often correlate with rank |
| Home region / state | **no** (not collected) | transfer patterns, language of check-in |
| Gender | **no** (not collected in v1) | leave-type mix; do not infer |
| Caste / religion | **no** — never collected | name, language, home-region proxies. Names live only in the identity vault and are **out of bounds** for scoring |
| Age band | yes (`age`) | consecutive-duty tolerance varies |

**Hard rule:** scoring code must never join `legal_name`. A PR that adds name/language/religion as a feature is rejected (AGENTS rule 9).

## 3. v1 rules audit (run on every ruleset change)

Use the ML-002 harness plus a seeded population (`python -m app.ml.harness`). Record:

| Check | Method | Pass bar |
|---|---|---|
| Alert rate by rank | `P(tier ≥ amber | rank)` | no rank's rate > 1.5× the unit rate without a documented operational reason (e.g. a CI company *is* higher-load — say so) |
| Alert rate by unit | `P(tier ≥ amber | unit)` | group-exposure flags (FR-08) must be the explanation when a unit spikes, not individual stacking |
| Score distribution | histogram 0–100 | no clipping pile-up at 100 |
| Masking rate by rank | `P(masking | rank)` | masking is a discrepancy detector; a rank-skewed masking rate is a red flag for instrument design, not "better detection" |
| Explanation coverage | every Amber+ flag has ≥ 1 factor with a resolvable i18n key | 100% |
| Firewall | commander scrape (TC-401/403) | 0 individual scores |

Fill the run log below. Invented percentages are forbidden — leave cells blank until measured.

## 4. v2 model audit (before any learnt model is served)

Protocol (Hardt, Price & Srebro 2016 — equality of opportunity as the baseline method):

1. **Stratify** precision, recall, and alert rate by rank, unit, age band. Gender/region only if those attributes exist *and* were lawfully collected for this purpose — they are not in v1.
2. **Proxy test:** train a probe classifier from the feature vector to rank / unit. If AUC ≫ chance, the features encode the attribute; drop or constrain the leaking features.
3. **Group-fairness constraint:** equalise *recall* across rank bands (FN cost is a life — we do not equalise by dropping sensitivity on a high-risk group). Record the FP cost this imposes (NFR-07).
4. **Human review sample:** 30 counsellor-labelled cases, 10 per rank band, before rollout.
5. **Publish** this checklist as a filled artefact in the repo. No silent skip.

Stop-ship: any rank/unit recall gap that cannot be explained by documented operational load.

## 5. SHAP report template (v2 — fill one page per scored case)

v1 explanations are rule factors (`risk.factor.*`). v2 must emit the **same sentence shape** with SHAP values substituted ([model-explainer.md](model-explainer.md) §5.4, Lundberg & Lee 2017).

```
SHAP case report
----------------
pseudonym:           ps_________
as_of:               ____-__-__
model:               lightgbm-survival / gbt  (circle)
model_version:       ________
base value (E[f]):   ________
output (risk / hazard): ________
tier (mapped):       green / amber / red / critical

Top SHAP contributions (signed):
  1. feature ________   value ________   φ = ________   i18n key ________
  2. feature ________   value ________   φ = ________   i18n key ________
  3. feature ________   value ________   φ = ________   i18n key ________

Plain-language (en):
  "Flagged because {1}, {2}, {3}."
Plain-language (hi):
  "..."

Fairness notes for this case:
  [ ] no name / religion / caste feature present
  [ ] rank used only as operational load context, not as a score input
  [ ] counsellor agrees the factors match the session  yes / no / deferred
```

Store filled reports next to `intervention_outcome` labels. They are the audit trail that NFR-05 still holds after the engine stops being a ruleset.

## 6. Run log

| Date | Engine | Population | Rank-gap | Masking-gap | Firewall | Notes |
|---|---|---|---|---|---|---|
| 2026-09-08 | rules v1.0 | seed demo (3BN + TINY) | not measured at battalion scale (demo n is small — Low confidence) | — | tests in `backend/tests/test_firewall.py` | Do not quote a fairness % from this demo seed |

## Links

[F04](../features/F04-risk-rules-engine.md) · [ML-002 harness](../../backend/app/ml/harness.py) · [ml-v2-data-collection-plan.md](ml-v2-data-collection-plan.md) · [shap-report-template.md](shap-report-template.md)
