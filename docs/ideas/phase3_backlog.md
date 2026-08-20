# Phase 3+ backlog

Items **shipped** (UI + analytics wired). Remaining work is polish, tests, or production hardening.

**Expanded scope for hiring showcase:** see [`../interview_showcase_plan.md`](../interview_showcase_plan.md) (calibration, conformal bands, knapsack, drift, SHAP, etc.).

## Shipped

- MMM adstock / seasonality / posterior predictive checks — [`analytics/attribution.py`](../analytics/attribution.py), [`pages/10_Attribution_MMM.py`](../pages/10_Attribution_MMM.py) (requires `requirements-mmm.txt`)
- Stochastic CM-NRR + conformal CPSO — [`analytics/stochastic_economics.py`](../analytics/stochastic_economics.py), Run Economics (rigorous mode)
- Conformal churn risk + cost_of_leaving bands — Radar / Decision Card (rigorous mode)
- Fitted hazard MLE + calibration lab — [`analytics/survival.py`](../analytics/survival.py), [`pages/34_Math_Lab_Calibration.py`](../pages/34_Math_Lab_Calibration.py)
- Decision-curve / net-benefit — [`analytics/decision_curves.py`](../analytics/decision_curves.py), [`pages/33_Math_Lab_Decision_Curves.py`](../pages/33_Math_Lab_Decision_Curves.py)
- Intervention knapsack under HITL capacity — [`analytics/knapsack.py`](../analytics/knapsack.py), Radar + Run Economics
- YAML bandit traffic + regret — [`analytics/bandits.py`](../analytics/bandits.py), Version Compare
- Permutation hazard attributions — Decision Card + Calibration lab
- Pareto-optimal Radar ranking — [`analytics/pareto.py`](../analytics/pareto.py), Radar (`radar_rank_mode` in profile priors)
- Contextual bandits (teaching Thompson) — Version Compare expander
- EVSI-driven `requires_review` — [`analytics/evidence.py`](../analytics/evidence.py), Decision Cards
- HITL M/M/c queueing (Erlang-C) — [`analytics/queueing.py`](../analytics/queueing.py), Run Economics
- Thin T-learner uplift — [`analytics/causal_uplift.py`](../analytics/causal_uplift.py) (`uplift_tlearner_gbm_v1` when n≥200)
- Calibrate `analytics/causal_model.py` from warehouse — Business Model chip when rigorous
- Competing risks cause-specific incidence — [`analytics/survival.py`](../analytics/survival.py), Taxonomy Browser
- Semantics posterior thresholds, Experiments CUPED/agentic design, Flags FDR — see Milestone A wiring
- Unit tests for bandits, queueing, pareto, stochastic_economics — `tests/unit/test_*.py`
- Interview kit + genAI contract — [`interview_kit.md`](../interview_kit.md), [`genai_for_math.md`](../genai_for_math.md)
- Q4 Tier 2 math — confidence sequences, drift lab, empirical Bayes harm, token VaR — see `analytics/inference/`, `analytics/drift.py`, `analytics/token_risk.py`
- Q4 Marketplace commerce vertical — `marketplace_agentic` preset, [`pages/35_Marketplace_Radar.py`](../pages/35_Marketplace_Radar.py)

## Still open

- Uplift forests via `econml` (beyond thin T-learner)
- Geo-holdout MMM calibration (needs geo panel in generator)
