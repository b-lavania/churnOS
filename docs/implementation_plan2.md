# ChurnOS Streamlit App Enhancement Plan

This plan outlines how to move the ChurnOS Streamlit app forward by incorporating the crucial findings from `docs/agenticchallenges.md`. The goal is to evolve the app from a general analytics interface into a highly specialized "Agentic Decision OS" that directly tackles the unique monetization, retention, and observability challenges of AI agents.

## User Review Required
> [!IMPORTANT]
> This plan focuses on enhancing the **Streamlit frontend** as requested. However, based on your previous goals of moving to a decoupled FastAPI backend with OTEL ingestion, please confirm if you want to build these new visualizations using the current synthetic data model first, or if we should start stubbing out the live API connections concurrently.

## Open Questions
> [!WARNING]
> 1. **Data Model Updates**: To power metrics like "Agent-to-Agent Coordination Overhead" and the "Cost Gantt Chart", we will need to extend the synthetic data generator (`core/`, `ontology/`). Should we update the synthetic generators as part of this plan, or focus strictly on the UI components with mock data first?
> 2. **Agentic Health Dashboard**: Should the new "Agentic Health" composite view replace the current `Radar` tab as the primary landing page, or sit alongside it as a new executive summary?

## Proposed Changes

We will systematically update the existing pages to reflect the 6 core challenges and introduce a unified executive dashboard.

---

### Phase 1: The "Agentic Health" Master Dashboard
Create a single pane of glass that combines the most critical signals across all dimensions, as recommended in the docs.

#### [MODIFY] `app.py`
- Update the primary landing experience (currently `Radar`) to feature an "Agentic Health" composite score.
- Color-code accounts (Red/Yellow/Green) based on a weighted combination of:
  - Cost-per-successful-outcome
  - TTFV (Time-to-first-value)
  - Integration depth score
  - Recent catastrophic events
- Add a "Data Source" toggle in the sidebar to switch between `Synthetic (Local)` and `Live (OTEL/FastAPI)` (stubbed for future integration).

---

### Phase 2: Run Economics & Cost Visibility
Address unpredictable costs and infrastructure blind spots.

#### [MODIFY] `pages/17_Run_Economics.py`
- **Jevons / Elasticity Chart**: Add a visualization showing Token Price vs. Total Token Volume to illustrate how cheaper tokens drive up overall consumption.
- **Agent Run Timeline (Gantt)**: Add a session-level Gantt chart showing tool calls, model invocations, and cumulative $ burned to expose hidden loops.
- **Unattributed Spend Gauge**: Add a metric showing the % of API cost that cannot be mapped to a specific agent or workflow (target <5%).

---

### Phase 3: Activation & Habit (The "First Win")
Address the phenomenon of activation failure disguised as churn.

#### [MODIFY] `pages/15_Activation_Habit.py`
- **Activation Funnel with Revenue**: Build a funnel showing Sign-up → First Paid Invoice → First *Verified* Successful Agent Outcome.
- **TTFV Distribution**: Add a histogram of days from first payment to first successful outcome.
- **"Paying but Dormant" Cohort**: Add a data table isolating users who are paying but haven't achieved a successful outcome in 14 days.

---

### Phase 4: Connectors & Switching Costs
Address the ease of ripping out wrapper apps.

#### [MODIFY] `pages/18_Connector_Blast_Radius.py`
- **Integration Depth Score**: Add a visualization scoring accounts based on connected systems, shared data volume, and agent memory length.
- **Context Decay Rate**: Add a metric showing how quickly churned users' context becomes useless (export rate vs retention).

---

### Phase 5: Trust, Approval & Non-Deterministic Success
Address catastrophic churn and opaque agent successes.

#### [MODIFY] `pages/16_Trust_Approval.py`
- **Catastrophic Event Log**: Add a timeline of severe agent failures (data deletion, bad comms) mapped against account churn.
- **Human Intervention Rate**: Add a time-series chart showing the % of runs requiring human takeover.

#### [MODIFY] `pages/20_Outcome_Flywheel.py`
- **Outcome Success vs. Complexity**: Add a chart plotting verified success rate against the number of agent steps/tool calls.
- **Coordination Overhead**: Add a metric showing tokens spent on agent-to-agent chatter vs. actual goal progress.

---

### Phase 6: Feature Flag Experimentation
Wire these metrics into the experimentation surface so every product decision is evaluated against cost, reliability, and retention.

#### [MODIFY] `pages/3_Conversion.py` (or a new Experimentation page)
- Integrate specific agentic flags (e.g., `max_retries_limit`, `guided_first_win_flow`, `agent_model_router_v2`) and show their direct impact on the new metrics (CPSO, TTFV, Human Intervention Rate).

## Verification Plan

### Automated Tests
- Run `pytest` to ensure no existing analytics logic is broken by adding the new metrics.
- Ensure the Streamlit app boots without errors (`streamlit run app.py`).

### Manual Verification
- Navigate through each updated page in the Streamlit UI to verify the new charts render correctly with the synthetic data.
- Verify that the new "Agentic Health" composite score dynamically updates when overriding decisions in the UI.
