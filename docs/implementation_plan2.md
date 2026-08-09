# Implementation Plan: The Agentic Retention Data Model (Phase 1 & 2)

You are completely right to call me out. The previous implementation plan jumped straight to building a generic SaaS application (FastAPI + React), which directly contradicts the roadmap laid out in `docs/methodology.md`. 

The methodology explicitly warns that "Dashboards don't prevent churn; interventions do" and that the productization decision (Phase 3) should only happen *after* the metrics generalize and interventions work for 2-3 qualifying design partners (friends). 

The real gap is **the join**, and the real deliverable right now is the **Data Model and the Intervention Loop**. Here is the corrected implementation plan that strictly follows your documentation.

## User Review Required

> [!WARNING]
> This plan abandons the premature "FastAPI/React" productization route and focuses entirely on executing Phase 1 and Phase 2 from `methodology.md`. We will build a **dbt project** to execute the critical joins and an **alerting engine** to drive interventions.

## Open Questions

1. **Warehouse Target:** For the initial dbt implementation (Phase 1), which data warehouse are we targeting? (e.g., Snowflake, BigQuery, Postgres, or duckdb for local testing?)
2. **Alerting Destination:** For Phase 2 (The Intervention Loop), where should the alerts be sent for the weekly review cadences? (e.g., Slack webhooks, email, or a simple generated markdown report?)

---

## Proposed Changes: Aligning with the Methodology

We will pivot from maintaining a Streamlit simulator to building a portable dbt project that can be deployed onto a design partner's existing data warehouse to prove the intervention loop.

### Phase 1: The Core Data Model (dbt Implementation)
The data model is the product. We will implement the schemas and the four critical joins as portable `dbt` models.

#### [NEW] `dbt_project/` (Root Directory)
Initialize a standard dbt project to handle the transformation layer on the partner's warehouse.

#### [NEW] `dbt_project/models/staging/`
Extract and normalize the raw exports from the three disjointed systems:
- `stg_langfuse_traces.sql` (Extracts `span_id`, `trace_id`, `tokens`, `cost`)
- `stg_stripe_billing.sql` (Extracts `subscription_id`, `mrr`, `usage_events`)
- `stg_app_outcomes.sql` (Extracts deterministic `outcome_type`, `verified_by`)

#### [NEW] `dbt_project/models/core/`
Implement the entities defined in §3.2 of the methodology:
- `dim_accounts.sql`, `dim_end_users.sql`, `dim_sessions.sql`
- `fct_agent_runs.sql`, `fct_spans.sql`
- `fct_outcomes.sql`, `fct_subscriptions.sql`

#### [NEW] `dbt_project/models/marts/`
Execute the "Critical Joins" (§3.3) and define the core metric aggregations (§4.2):
- `mart_account_agentic_health.sql`: Joins AgentRuns -> Outcomes -> Subscriptions to compute:
  - **Delegation Ratio**
  - **Autonomy Ratio**
  - **Cost per Successful Outcome (CPSO)**
  - **Contribution-Margin NRR (CM-NRR)**

---

### Phase 2: The Intervention Loop (Alerting & Reporting)
We will build a lightweight Python engine to run on top of the dbt marts, executing the alerting rules that actually prevent churn.

#### [NEW] `interventions/` (Directory)
A module dedicated to surfacing actionable insights, rather than just dashboarding.

#### [NEW] `interventions/rules.py`
Implement the hardcoded alerting thresholds defined in Phase 2:
- Delegation ratio drops > 15% WoW.
- Autonomy ratio drops > 10% over 4 weeks.
- Cost-per-outcome exceeds pricing margin.
- Tourist Alert: Active account, but no verified outcome in 14 days.

#### [NEW] `interventions/taxonomy_classifier.py`
Implement the Churn Taxonomy (§4.3) to auto-tag accounts with reason codes (`tourist`, `value_failure`, `efficiency`, `displacement`, `price`) based on the dbt mart trends.

#### [NEW] `interventions/weekly_report.py`
A script that generates the "Weekly account health report" (a markdown or PDF document) for the 30-minute review cadence with design partners. 

---

### Sunsetting the Simulator
To fully commit to this path, the synthetic components must be quarantined or removed.

#### [MODIFY] `data/agentic_generator.py`
- Deprecate the synthetic data generator. It has served its purpose for the demo.
- Replace with a `dbt seed` approach that loads a small, static set of mock CSVs into the warehouse just for local CI/CD testing of the dbt joins.

#### [MODIFY] `app.py` & `.streamlit/`
- Freeze feature development on the Streamlit dashboard. 
- It remains available purely as a "pitch deck" visualization tool for acquiring the Phase 0 design partners, but it is not the product architecture moving forward.

---

## Verification Plan

### Validation Phase
1. **Compile & Run dbt:** Execute `dbt build` against a local DuckDB or Postgres instance seeded with mock Langfuse and Stripe data.
2. **Verify Critical Joins:** Ensure `mart_account_agentic_health.sql` correctly attributes token costs from a trace span all the way up to an account's MRR to calculate the `CM-NRR` metric.
3. **Trigger Interventions:** Run `interventions/weekly_report.py` and verify it correctly flags an account as a `value_failure` if their outcome success drift drops while their cost-per-outcome spikes.
