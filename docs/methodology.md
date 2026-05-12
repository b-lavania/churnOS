## Methodology, assumptions & limitations (`churnOS`)

This appendix explains how simulated data behaves, where inference is causal vs associational,
and how product-analytics proxies should be read.

### Synthetic data lineage

Customer, transaction, funnel, behavioural-event, marketplace, and marketing aggregates are emitted by
[`data/generator.py`](../data/generator.py).
Parameters on each Streamlit surface shift means and volatilities, but correlation structure is authored,
not scraped from warehouse facts.

Use this codebase to stress-test **reasoning pipelines**, never to certify production forecasts without
offline validation on real instrumentation.

### Churn vs purchase-based retention triangles

Operational churn badges are derived from probabilistic churn flags tied to signup span.
Monthly retention triangles recombine **transaction timestamps** relative to signup cohort months.
Treat them as behavioural retention of buyers, distinct from invoiced SaaS contraction.

Kaplan–Meier curves elsewhere further separate segment survival.

### Random Forest churn “drivers”

Feature importance captures **association** conditioned on labelled synthetic churn—not causal uplift from
pricing, policy, or product experiments. Interpret as prioritised exploratory axes, never as guaranteed levers.

### Bayesian Marketing Mix Models (MMM)

PyMC notebooks model aggregate response curves with diminishing returns assumptions.
MMM answers “how incremental channel spend statistically relates to blended sales proxies,” not granular
experiment-level attribution. Confounding spend with macro seasonality violates identification quickly.
Always pair MMM storyline with disciplined lift tests wherever feasible.

### Product analytics layer specifics

Activation windows classify first **net-revenue-positive** purchases within `{7/14/28}` days—stockouts that
produce zero-net rows never count toward activation milestones.

Stickiness analogue (`analytics/product_metrics.py`) compares weekly unique purchasers vs mean daily purchasers;
it substitutes for app DAU/WAU absent client telemetry—label dashboards accordingly.

Instrumentation simulator events (`product_events`) exist to demo sessionization/adoption calculus, not pixel-perfect web analytics.

### Experiments ↔ economics read-through helpers

Thin helpers translate relative session conversion lifts using session counts and causal-model outputs.
Treat numbers as illustrative unless powered by calibrated incrementality experiments and guardrail metrics
such as refunds, discount leakage, latency, fraud, cannibalisation, or margin compression.

North Star narratives should align with an **overall evaluation criterion (OEC)** plus explicit guardrail
tiles; uplift stories from MMM, incrementality lifts, or product onboarding metrics must reconcile to avoid double counting.
