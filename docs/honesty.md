# Honesty & limits (synthetic demo)

churnOS is a **synthetic teaching environment**. Numbers illustrate methodology and decision workflows; they are not production telemetry.

## What is real vs simulated

| Layer | Status |
| --- | --- |
| Warehouse tables | Fully synthetic (`data/agentic_generator.py`) |
| Metric formulas | Teaching definitions aligned to `docs/methodology.md` |
| GDR exceptions | Heuristic classifiers on synthetic signals |
| Causal claims | Only when `experiment_id` is present on a record |
| Outcome flywheel | Simulated write-back using generator ground truth |

## Associational vs causal

- **Associational:** correlation-style signals (usage ↔ churn uplift, drift WoW). Shown with confidence, not causal verdicts.
- **Causal gate:** `subject.experiment_id` + experiment tables. Without it, records must not claim causal harm.
- **Human override:** `decision.final_action` may differ from `recommended_action`; flywheel compares followed vs overridden cohorts.

## Teaching formulas

- **Cost of leaving live** (`economics.primary_metric_usd`): rollup of LTV-at-risk + run cost for capabilities; LTV teaching formula for accounts.
- **CM-NRR:** contribution-margin net revenue retention on synthetic subscriptions.
- **$/successful outcome:** gross run cost / verified successful outcomes in window.

## Data storage

- GDR audit trail: JSONL via `ontology/store.py` (local, run-as-you-go).
- No raw prompts stored (methodology §3.4).

For the full retention methodology, see [`methodology.md`](methodology.md).
