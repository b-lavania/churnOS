# Math dojo contributor guide

Every rigorous method in churnOS ships as:

1. **Pure function** in `analytics/` (no Streamlit)
2. **Unit + property tests** in `tests/`
3. **Math Lab** page under LEARN nav (optional for backlog items)
4. **DECIDE/LEARN hook** — operator-facing so-what on Radar, Version Compare, or Flywheel
5. **Optional `evidence` block** on GDR exceptions when `profile.priors.math_mode == "rigorous"`

## Ground truth

`data/ground_truth.py` stores planted latents per seed. Tests assert estimators recover truth within tolerance.

## Honesty

- `claim_type: causal` requires `experiment_id` — see `docs/honesty.md`
- Default `math_mode` is `heuristic`; toggle on Product Profile

## Modules

| Module | Estimand | UI surface |
| --- | --- | --- |
| `analytics/inference/binomial.py` | churn rate posterior | Math Lab Binomial |
| `analytics/survival.py` | P(churn_30d), cost bands | Weekly Report, Decision Card |
| `analytics/experimentation.py` | clustered sample size, CUPED, FDR | Math Lab Power |
| `analytics/agent_version_compare.py` | SPRT version decision | Version Compare |
| `analytics/causal_uplift.py` | uplift_pp | capability_harm evidence |
| `analytics/clv_probabilistic.py` | BG/NBD CLV (legacy) | Math Lab CLV |

Teaching UI hooks without dedicated tests yet: `bandits`, `queueing`, `pareto`, `stochastic_economics`, `flag_segments` — follow the contract above when adding coverage.

## Acceptance per PR

Analytics + tests + at least one DECIDE/LEARN surface + estimand gloss in `ui/explain.py`.
