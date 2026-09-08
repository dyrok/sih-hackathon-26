# Model Explainer — Risk Engine v1 and the ML v2 Roadmap

> Owner: kv · Status: [x] current · Last updated: 2026-09-08
> Diátaxis: explanation ("why it works"), not how-to. The full rule table and threshold values live in [F04](../features/F04-risk-rules-engine.md); this page explains the reasoning behind them.

## 1. Why rules v1, not ML — owning the zero-labels position

On day one there is **zero labelled outcome data** on stress and burnout for Indian CAPF personnel: no dataset connects features ("days since leave", "sleep trend") to verified outcomes ("deteriorated", "recovered after intervention"). Any accuracy figure quoted for a model trained without labels would be fabricated — a judged SIH red flag and an ethical failure ([ADR-0001](../architecture/decisions/0001-rules-engine-v1-not-ml.md)).

v1 is therefore a **clinically grounded, transparent rules engine**:

- every threshold traces to a validated instrument or a published clinical convention (see [clinical-instruments.md](clinical-instruments.md));
- every alert ships with its top contributing factors (FR-06, [PRD](../product/prd.md));
- the whole decision logic is readable in one document — explainability by construction, not by post-hoc surgery on a black box.

We state this openly rather than dressing v1 up as "AI". v1's honest claim is **structured, defensible, explainable triage**. ML is deferred, not skipped: v2 trains once counsellor session outcomes accumulate as labels (human-in-the-loop), with scikit-learn/LightGBM + SHAP reserved from day one of the stack ([ADR-0006](../architecture/decisions/0006-tech-stack.md)).

## 2. Signal triangulation — three weak sources beat one strong one

v1 scores risk from three independent sources read **together**:

| Source | Strength | Blind spot |
|---|---|---|
| Self-report (check-ins, instruments) | Rich symptom detail; voluntary | Under-reporting is the norm in a high-stigma force |
| HR signals (leave, roster, deployment) | Zero-effort, objective, always present | Captures circumstances, not inner state |
| Passive signals (on-device prosody, [F03](../features/F03-on-device-signals.md)) | Continuous, non-intrusive, opt-in | No clinical validation in this population; weighted low ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)) |

Each source alone is unreliable; the triangulation is the model. **Discrepancy is a feature, not noise** (FR-07): "I am fine" + 4h sleep + 60 duty days + 2 cancelled leaves = a **masking flag**. In a high-stigma organisation, someone hiding distress is a *higher* risk than their self-report admits — the faking is the finding, not a data-quality problem. The survey-side defences (validity-scale items, response-pattern detection) are described in [clinical-instruments.md](clinical-instruments.md).

## 3. Per-person baselines — change-point detection, not absolute thresholds

Absolute thresholds fail across age, rank, and role: a havildar with chronic insomnia and a newly posted constable do not share a "normal". A jawan whose sleep drops from 7h to 4.5h is a signal; a jawan who has always slept 5h is not.

v1 therefore scores each person against **their own trailing baseline** (rolling window; exact span is a tuned parameter, ML-002) and asks *how much, and how fast, did this person deviate from themselves* — classic change-point detection. Cheap detectors (EWMA, CUSUM) cover v1; the proper change-point machinery (PELT — Killick, Fearnhead & Eckley 2012) is the v2 upgrade on the same framing.

Deviations that feed the score: consecutive duty days vs the person's own norm, days-since-leave vs their leave history, circadian disruption vs their shift history, sleep/self-report slope vs their baseline.

## 4. How v1 scores (summary — full rule table in F04)

- Triangulated signals → weighted rules → composite risk 0–100.
- Output maps to the intervention ladder Green → Amber → Red → Critical (FR-09), capacity-aware triage (FR-10), [F05](../features/F05-intervention-engine.md).
- Voice/prosody features enter weighted **low** — unvalidated in this population ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)).
- Group trauma exposure (a unit casualty/incident) auto-flags the whole exposed group, never individuals (FR-08).
- Full rule table with clinical citations: [F04](../features/F04-risk-rules-engine.md) · backtest harness: `python -m app.ml.harness` (ML-002, seed DEMO-PERSONA-01). Fairness checklist: [fairness-audit-checklist.md](fairness-audit-checklist.md). v2 labels: [ml-v2-data-collection-plan.md](ml-v2-data-collection-plan.md).

## 5. The v2 roadmap — same problem, now with labels

### 5.1 Labels come from counsellor outcomes (human-in-the-loop)
Once [F06](../features/F06-counsellor-console.md) session-outcome tracking accumulates real outcomes (did the person improve after intervention?), those become training labels. Labels are outcomes of care, not guesses — and humans stay in the loop by construction.

### 5.2 Model choice by data shape, not fashion
- **Tabular HR features** (days-since-leave, transfer count, cancelled leaves…) → **gradient-boosted trees** (LightGBM — Ke et al. 2017; XGBoost — Chen & Guestrin 2016): best-in-class on small-to-medium tabular data, native SHAP support.
- **Roster/leave time series** (shift patterns, deployment cadence) → **temporal model** — kept only if it beats gradient boosting on engineered lagged features. The data shape decides; the hype does not.

### 5.3 Survival analysis is the honest framing
The real question is not "is this person stressed today" but **time to burnout event** — a survival-analysis problem (Cox 1972). This is genuinely the right shape because:
- the outcome is *when*, not *whether* — risk rises and falls across a career;
- **right-censoring is native**: personnel who resign, transfer, or are not yet in distress are handled correctly instead of counted as "negatives";
- a **per-person hazard curve** reads naturally for a counsellor: risk now, trend, horizon.

### 5.4 Explainability stays mandatory — SHAP
At v2, SHAP (Lundberg & Lee 2017) attributes each prediction to its features: *"flagged because 47 consecutive duty days, 2 cancelled leaves, sleep down 30% vs own baseline."* v1's plain-language rule explanations graduate into SHAP-attributed versions of the same sentence — the format never breaks, only the attribution engine improves (NFR-05).

### 5.5 Fairness audit before any rollout
Prove the model does not systematically flag by **rank, region, gender, or caste/religion proxies** (home region, name, language). Protocol: stratify alert rates, precision and recall by subgroup; test proxy features explicitly; use group-fairness constraints (Hardt, Price & Srebro 2016) as the baseline method; publish the audit as an artifact. A model that flags certain states or communities more often is a fairness failure even if it "predicts" well — flagged-and-stigmatised personnel are the harm, not a rounding error. Checklist owner: ML-003.

### 5.6 Cost framing: FP/FN economics, said out loud
- **False positive** = one unnecessary cup of tea with a counsellor.
- **False negative** = a life (cf. the reported CAPF suicide toll — [datasets-research.md](datasets-research.md)).

Thresholds are tuned **asymmetrically toward sensitivity**, with alert caps to prevent fatigue (NFR-07). We say this on the deck slide, not in a footnote: the right operating point of this system is deliberately "annoying but safe".

## 6. What would falsify this approach (honest limitations)

- **If counsellor outcomes accumulate and the rules do not predict them.** The rule table is a hypothesis; if v2 labels show the rules add no signal, we say so and replace them. The rules are a floor, not a faith.
- **Baselines break under legitimate change.** Posting, promotion, or family events shift a person's baseline; the engine must not score adaptation as deterioration (test case in [test-plan.md](../quality/test-plan.md)).
- **Masking detection is a heuristic** against a social pattern. A false "faking" flag damages trust, so discrepancy flags stay low-severity in v1.
- **Passive/voice features are unvalidated in this population.** If their weights cannot be defended, they are dropped rather than defended ([ADR-0002](../architecture/decisions/0002-on-device-voice-inference.md)).
- **Rules lag rather than anticipate** sudden crises. v1 is early-warning support for humans, never an autonomous gatekeeper — welfare-not-discipline firewall ([ADR-0003](../architecture/decisions/0003-two-tier-output-k-anonymity.md)).

## Sources

- Killick R, Fearnhead P, Eckley IA (2012) — Optimal detection of changepoints (PELT), JASA 107(500).
- Cox DR (1972) — Regression models and life-tables, JRSS-B 34(2).
- Lundberg SM & Lee SI (2017) — A unified approach to interpreting model predictions (SHAP), NeurIPS 30.
- Ke G et al. (2017) — LightGBM, NeurIPS 30 · Chen T & Guestrin C (2016) — XGBoost, KDD.
- Hardt M, Price E, Srebro N (2016) — Equality of Opportunity in Supervised Learning, NeurIPS 30.
- Barrett LF et al. (2019) — Emotional expressions reconsidered (contested inference science), Psychological Science in the Public Interest 20(1).
