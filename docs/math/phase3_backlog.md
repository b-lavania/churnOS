# Phase 3+ backlog

Items **shipped** (UI + analytics wired). Remaining work is polish, tests, or production hardening.

## Shipped

- MMM adstock / seasonality / posterior predictive checks — [`analytics/attribution.py`](../analytics/attribution.py), [`pages/10_Attribution_MMM.py`](../pages/10_Attribution_MMM.py) (requires `requirements-mmm.txt`)
- Stochastic CM-NRR + conformal CPSO — [`analytics/stochastic_economics.py`](../analytics/stochastic_economics.py), Run Economics (rigorous mode)
- Pareto-optimal Radar ranking — [`analytics/pareto.py`](../analytics/pareto.py), Radar (`radar_rank_mode` in profile priors)
- Contextual bandits (teaching Thompson) — [`analytics/bandits.py`](../analytics/bandits.py), Version Compare expander
- EVSI-driven `requires_review` — [`analytics/evidence.py`](../analytics/evidence.py), Decision Cards
- HITL M/M/c queueing (Erlang-C) — [`analytics/queueing.py`](../analytics/queueing.py), Run Economics
- Thin T-learner uplift — [`analytics/causal_uplift.py`](../analytics/causal_uplift.py) (`uplift_tlearner_gbm_v1` when n≥200)
- Calibrate `analytics/causal_model.py` from warehouse — Business Model chip when rigorous
- Competing risks cause-specific incidence — [`analytics/survival.py`](../analytics/survival.py), Taxonomy Browser
- Semantics posterior thresholds, Experiments CUPED/agentic design, Flags FDR — see Milestone A wiring

## Still open

- Uplift forests via `econml` (beyond thin T-learner)
- Production bandit rollout policy (YAML-governed traffic allocation)
- Geo-holdout MMM calibration (needs geo panel in generator)
- SHAP explainability on hazard models
- Dedicated unit tests for bandits, queueing, pareto, stochastic_economics, flag_segments

Track in issues when prioritizing.
