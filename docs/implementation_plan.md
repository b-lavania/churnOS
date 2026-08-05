# Agentic Decision OS: The "Amplitude + ChartMogul for Agents"

This plan outlines the architecture for evolving ChurnOS from a synthetic heuristic simulator into a true, decision-grade analytics and control plane for agentic builders. It bridges the gap between raw LLM traces (LangSmith/Braintrust) and business outcomes (Amplitude/ChartMogul), anchored by our unique **Ontology as IP**.

**Product posture:** churnOS is an **open-source toolkit** for builders evaluating agentic product economics and retention — not a commercial SaaS we charge for. Economics simulations model *the builder's* product (their seats, their inference burn, their billing model), not churnOS licensing.

---

## 0. Current State (What Already Exists)

| Area | Status | Key artifacts |
| --- | --- | --- |
| **Ontology IP** | ✅ Shipped | `ontology/exception_taxonomy.py` (incl. loop/quality/eval/confirmation), semantics, GDR schema |
| **Agentic Product Profile** | ✅ Shipped | presets + `billing_model` / `api_metered` |
| **Synthetic warehouse** | ✅ Shipped (v2.1) | loops, steps, tokens, `outcome_confirmed`; `connector_capability_graph`; `eval_results` |
| **Economics engine** | 🟡 Partial | `analytics/economics.py` + `data/pricing_oracle.yaml` |
| **Decision engine** | ✅ Shipped (heuristic+) | classify includes loop/quality/confirmation; trend pre-step |
| **Decision surfaces + viz** | ✅ Shipped | charts on Activation / Trust / Run Economics / Connectors |
| **Sidebar nav** | ✅ Shipped | short TOC; Legacy index; no expand_more clutter |
| **Outcome flywheel** | ✅ Shipped (demo) | JSONL store |
| **OTEL mock** | ✅ Shipped | `data/otel_mock_generator.py` |
| **Ingestion parsers / FastAPI / Causal PyMC** | ⬜ Not started | see §9 open list |

**Honesty contract (do not regress):** Synthetic limits and associational vs causal rules must stay visible in-product. Note: [`docs/methodology.md`](methodology.md) is now the **Agentic Retention System** data-model/metric plan (Account→Outcome→Revenue). Alignment / rebuild sequencing lives in [`docs/build_plan_from_methodology.md`](build_plan_from_methodology.md).

---

## 1. Gap Analysis & Resolved Decisions

Seven gaps identified in the prior draft, now resolved with industry-grounded answers.

### Gap 1 → Loop Modeling (RESOLVED)

**Industry reality:** Agent execution is **not** a sequence of independent runs. It follows a Perceive → Reason → Act → Observe → Loop cycle. Loop depth distributions are bimodal: ~70% of tasks complete in 1–3 steps, but the remaining ~30% that encounter tool errors or planning failures spiral to 6–12+ steps ("reasoning thrash"). At 8+ steps on GPT-4o-class models, a single user task can cost 10–50× more than expected.

**Decisions:**
- Add `loop_count` and `steps_to_completion` to the `agentic_generator.py` run schema (bimodal distribution: geometric(p=0.7) for normal, geometric(p=0.15) for failure paths).
- Add `loop_exhaustion` to `exception_taxonomy.py` — triggered when `loop_count > profile.max_loops_threshold`.
- Token economics formula becomes: `run_cost_usd = Σ(tokens_per_step × step_count × unit_price) - cache_credit`. Cache credit is significant: steps 2+ often reuse 60–80% of the prior context.

**New taxonomy entry:** `loop_exhaustion` | owner: `engineering` | severity: `high` | hint: "Agent exceeded loop budget; inspect planning step for goal drift or tool-call hallucination."

### Gap 2 → Output Quality Signal (RESOLVED)

**Industry reality:** Binary `success=True/False` is a liveness check, not a quality check. The industry converges on two upstream quality signals:
1. **Downstream task completion** — did the artifact produced by the agent get used? (email actually sent, CRM record actually saved). This is the strongest signal but requires connector-level confirmation events.
2. **Step efficiency** — `steps_to_completion` relative to a capability's historical baseline. High step counts are the earliest detectable warning of output quality degradation, appearing before users churn or leave feedback.

Thumbs-up/down feedback (Braintrust/LangSmith pattern) is valuable but has < 5% response rates in production; it cannot be the primary signal.

**Decisions:**
- Add `steps_to_completion` to run schema (already aligned with Gap 1).
- Add `outcome_confirmed` boolean to connector events — set `true` when a downstream write event (e.g., `email_sent`, `crm_updated`) is observed within 60s of run success.
- New exception: `quality_drift` — triggered when `mean(steps_to_completion)` for a capability exceeds its 28d baseline by > 1.5σ. Owner: `data_science`.
- Metric added to lexicon: `steps_per_successful_task` (lower is better; guardrail metric).

### Gap 3 → Eval Governance Vertical (RESOLVED)

**Industry reality:** `eval_drift` is the #1 silent killer of agentic products. When a provider releases a new model version (e.g., GPT-4o → GPT-4o-mini migration) or a team changes a system prompt, offline eval scores may hold but online task success rates degrade. ~89% of teams now treat golden-set regression as a CI gate.

**Decision:** Activate `eval_governance` in **P3** (same phase as causal engine), not deferred. It is a natural fit because the causal engine needs ground truth labels — the golden-set IS the ground truth.

**New artifacts:**
- `eval_results` table in `Workspace`: `(capability_id, capability_version, eval_suite_id, score, evaluated_at)`.
- `eval_drift` exception activated in `classify()`: triggered when `eval_results` score drops > 10% from the prior version baseline.
- New page: `pages/24_Eval_Governance.py` — shows score trend per capability version, flags regression.

### Gap 4 → Connector Dependency Graph (RESOLVED)

**Decision:** Make it a **first-class derived table**, computed once at workspace build time and cached, not re-derived at query time per page. Rationale: query-time joins across `connector_events` × `runs` × `capabilities` are O(n²) and will be slow at 10k+ runs.

**New artifact:** `connector_capability_graph` DataFrame added to `Workspace`:
```
connector_id | capability_id | call_count | fail_count | blast_radius_seats
```
Built in `core/workspace.py` by joining `connector_events → runs → seats`. The Connector Blast Radius page reads this directly instead of doing ad-hoc groupby. "If Gmail fails, these 4 capabilities are affected for these N seats" becomes a single lookup.

### Gap 5 → Experiment Court → GDR Bridge (RESOLVED)

**Decision:** The experiment subject should be `capability_version`, not funnel steps. The Experimentation Court (`pages/3_Conversion.py`) is legacy. A new, purpose-built **Capability Experiment surface** should be added at `pages/25_Capability_Experiment.py`.

**Flow:**
1. Builder creates an experiment: assigns seats to `control` (CAP-001-v1) vs `variant` (CAP-001-v2).
2. Both versions run; outcomes collected in `experiment_assignments` + `experiment_outcomes` (already in warehouse).
3. After N days, system runs Bayesian A/B test on `weekly_delegation_habit` and `churn_happened` as primary outcomes.
4. If `variant` wins, a GDR is emitted with `verdict=healthy`, `recommended_action=ship`, and `subject.experiment_id` set — making the causal claim defensible per the methodology honesty contract.

This closes the loop: experiments produce evidence → evidence upgrades GDR confidence.

### Gap 6 → Time-Series Trending (RESOLVED)

**Industry reality:** Point-in-time verdicts are useless for operational decisions. The signal is trajectory. A trust incident rate of 4% is fine; 4% trending to 8% over 3 weeks requires immediate action.

**Decision:** Introduce `evaluation_windows` — trailing 7d, 14d, 28d snapshots stored in JSONL alongside the GDR. Each GDR gets a `trend` field:
```json
"trend": {
  "metric": "trust_incident_rate",
  "direction": "worsening",
  "slope_per_week": 0.018,
  "weeks_to_threshold": 2.4
}
```
The decision engine computes slope via simple linear regression over the window. `worsening` + `weeks_to_threshold < 4` upgrades verdict severity by one level (e.g., `leaking` → `destructive`).

Generator produces time-stamped runs already (2-year range). Window aggregation is added to `analytics/decisions.py` as a pre-classification step.

### Gap 7 → Landing Page (RESOLVED)

**Decision:** `index.html` ships **pre-P4** with portfolio design language ([blavania.netlify.app](https://blavania.netlify.app): DM Sans/Mono, teal tokens, zero-radius cards). Copy sells the shipped OSS toolkit only — Profile → Radar → GDR loop, honesty chips for synthetic data — and does **not** claim FastAPI control plane or causal PyMC. P4 may later add control-plane receipts to the same page. Keep it as a static file (no framework needed).

### Gap 8 → Initial Seeded Values Flow (RESOLVED)

**Industry reality:** The current flow uses a legacy Streamlit sidebar (`pages/00_Agentic_Product_Profile.py`) to take user inputs (`preset_id` and `seed`), which are saved to `st.session_state` and fed synchronously into `build_workspace()` to generate the synthetic warehouse. This is a toy model. A production agentic control plane needs to accept continuous asynchronous trace ingestion via API.

**Decision:** We will decouple ingestion from the UI.
1. **Short term (P1):** The UI sliders stay for demo purposes but will trigger the new `data/otel_mock_generator.py` to write synthetic OTEL traces to disk (JSONL/DuckDB) rather than returning a pandas DataFrame directly to session state.
2. **Long term (P4):** The FastAPI `/v1/traces/ingest` endpoint becomes the primary entry point. The UI simply queries the backend for the current state of the warehouse.

### Gap 9 → UI Architecture Pivot Beyond Streamlit (RESOLVED)

**Industry reality:** A mere sidebar layout change in Streamlit will never feel like a high-end SaaS product (Amplitude/ChartMogul). Streamlit is excellent for rapid data prototyping but terrible for complex, decoupled web app routing, state management, and bespoke visual design.

**Decision:** The Streamlit app will be relegated to an "Internal Debug / Admin View." For the true SaaS experience, we will pivot to a decoupled architecture in **Phase 4**:
- **Backend:** FastAPI serves all metrics, topology graphs, and decision records via JSON.
- **Frontend:** A modern, decoupled web frontend (e.g., Next.js, React, or Vanilla HTML/JS with rich components) will consume the FastAPI endpoints. This removes all Streamlit sidebar constraints and allows for a true premium SaaS UI (top nav, persistent filters, custom interactive visualizations).

### Gap 10 → Activation Failure Disguised as Churn (RESOLVED)

**Industry reality:** Agentic products have ~40% revenue retention not because the "magic fails", but because users never achieve a clear first win. Paying users poke around and leave. Classic metrics (DAU, feature clicks) fail. The true leading indicators are Time-to-First-Value (TTFV) and "paying but dormant" cohorts.

**Decision:**
- Add `time_to_first_value` and `paying_but_dormant_rate` to the ontology.
- Introduce an Activation Funnel (Sign-up → Paid → First Verified Success) and a TTFV histogram to `pages/15_Activation_Habit.py`.
- New taxonomy exception: `activation_failure` — triggered when a high percentage of paying accounts cross 14 days with zero successful outcomes.

### Gap 11 → Cost Opacity & The Jevons Paradox (RESOLVED)

**Industry reality:** Token costs deflate ~10x/year, but cheaper tokens drive *more* consumption (longer context, more loops). Total bills rise even as unit prices fall, destroying margins for power users. Furthermore, teams lack attribution, leading to high "unknown spend."

**Decision:**
- Add `unattributed_spend_percentage` and `power_user_margin_leakage` to the metrics lexicon.
- Introduce a Jevons Elasticity chart (Cost vs Volume) and an Agent Run Timeline (Gantt chart with cost overlays) to `pages/17_Run_Economics.py`.
- New taxonomy exception: `margin_leakage` — triggered when the top 5% of users by token volume show negative contribution margin.

### Gap 12 → Low Switching Costs & Integration Depth (RESOLVED)

**Industry reality:** Pure prompt wrappers have zero switching costs and suffer massive churn. Deep integrations and accumulated context create moats.

**Decision:**
- Add `integration_depth_score` to the ontology (a composite of connector count, data volume, and memory lifespan).
- Surface this score and a "Context Decay Rate" chart on `pages/18_Connector_Blast_Radius.py` to identify accounts at high risk of ripping out the product.

### Gap 13 → Catastrophic Reliability Shocks (RESOLVED)

**Industry reality:** Trust isn't just about small errors; it's about catastrophic failures (e.g., agent deletes a DB) which lead to permanent churn.

**Decision:**
- Add `catastrophic_event_rate` and `human_intervention_rate` to the ontology.
- Update `pages/16_Trust_Approval.py` to feature a Catastrophic Event Log timeline mapped against account churn and post-failure trust drops.
- New taxonomy exception: `catastrophic_failure` — triggered immediately upon any irreversible negative agent action.

---

## 2. Revised Architecture

```
+----------------------------------------------------------+
|              Layer 1: Ingestion & Topology               |
|  OTEL / Trace Ingestion  -->  PII / Prompt Scrubbing     |
|  Loop Modeler            -->  Connector Dep. Graph        |
|  Lineage Resolver        -->  Topological Mapper         |
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|              Layer 2: Economics Engine                   |
|  Token Pricing Oracle    -->  Loop-Cost Calculator       |
|  Dual Billing Simulator  -->  Margin & COGS Engine       |
|  Outcome Confirmation    -->  Cache Credit Model         |
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|             Layer 3: Causal Decision Engine              |
|  Bayesian Churn Model    -->  Cold-Start Policy          |
|  Quality Drift Detector  -->  Eval Governance Gate       |
|  Trend / Window Engine   -->  Experiment-GDR Bridge      |
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|             Layer 4: Control Plane & UI                  |
|  FastAPI Machine API     -->  Streamlit Debug View       |
|  Dynamic Webhooks        -->  Topology / Graph Viz       |
|  Decision Card v2        -->  Visual receipts (ui/viz)   |
|  Capability Experiment   -->  Eval Governance Page       |
+----------------------------------------------------------+
```

---

## 3. Updated Ontology: New Metrics & Taxonomy Entries

### New exception categories (add to `exception_taxonomy.py`)

| Key | Owner | Severity | Playbook hint |
|---|---|---|---|
| `loop_exhaustion` | engineering | high | Agent exceeded loop budget; inspect planning step for goal drift or tool-call hallucination. |
| `quality_drift` | data_science | high | Steps-to-completion trending up; output quality degrading before users notice. |
| `eval_regression` | data_science | high | Offline eval score dropped >10% from prior version; do not ship until re-evaluated. |
| `outcome_confirmation_gap` | product | medium | Run succeeds but downstream write events not observed; agent may be producing orphaned artifacts. |
| `activation_failure` | product | high | High % of paid accounts reaching 14 days without a verified successful outcome. Force guided first-win flow. |
| `margin_leakage` | finance | high | Power users generating negative contribution margin due to context bloat or retry loops. |
| `catastrophic_failure` | engineering | critical | Irreversible negative action (e.g., data deletion). Immediate rollback and trust intervention required. |

### New metrics (add to `metrics/lexicon.yaml`)

| Key | Type | Role | Caveat |
|---|---|---|---|
| `steps_per_successful_task` | guardrail | guardrail | Lower is better. Baseline at 28d p50 per capability. |
| `loop_exhaustion_rate` | guardrail | guardrail | Runs hitting max_loops / total runs. |
| `outcome_confirmation_rate` | product | leading | Downstream write events / successful runs. |
| `eval_score_delta` | economics | signal | Current eval score minus prior version score. |
| `capability_trend_slope` | economics | signal | Weekly drift in primary guardrail metric. |
| `time_to_first_value` | product | leading | Median days from first payment to first verified successful outcome. |
| `paying_but_dormant_rate` | revenue | lagging | % of paying accounts with 0 successful outcomes in trailing 14d. |
| `integration_depth_score` | retention | leading | Composite score of connected systems and context memory lifespan. |
| `unattributed_spend_percentage` | economics | guardrail | Share of token cost lacking workflow/agent attribution tags. Target <5%. |
| `human_intervention_rate` | product | signal | % of runs requiring human takeover. |

---

## 4. Phased Roadmap (Revised)

| Phase | Goal | Status | New work from gap analysis |
| --- | --- | --- | --- |
| **P0 — Bridge** | Portfolio demo stays working | ✅ Done | Sidebar nav fix (§6A): `expanded=True`, hide chevrons, shorten titles, demote LEGACY |
| **P1 — Ingestion MVP** | Mock OTEL → warehouse with loops | ✅ Core done | Loop-count bimodal generator; connector dep. graph; `outcome_confirmed`; OTEL mock JSONL; loop hist + blast graph viz |
| **P2 — Economics** | Token math + loop-cost model | 🟡 Started | Oracle YAML; `analytics/economics.py`; dual billing toggle on Run Economics; waterfall viz. Full Stripe-free dual sim OK; Radar tornado still open |
| **P3 — Causal v1 + Eval** | PyMC + eval governance | ⬜ Pending | Eval page; causal agent; trend engine scaffolded in P1 (`analytics/trend_engine.py`) |
| **P4 — Control plane** | FastAPI + webhooks + landing page | 🟡 Partial | Landing (`index.html`) shipped; API still open |
| **P5 — Production hardening** | Auth, retention, deploy | ⬜ Pending | Tenant isolation; Docker compose |

---

## 5. Execution Guide (Detailed Code-Level Instructions)

This section provides explicit instructions for a junior engineer or LLM to implement the changes without ambiguity. Follow these steps exactly.

### Layer 1: Ingestion & Ontology

#### [MODIFY] `data/agentic_generator.py`
- **Function:** `generate_agentic_warehouse(profile, seed)`
- **Logic:**
  1. Add a `loop_count` column to the `runs` DataFrame. Use `np.random.geometric(p)`:
     - For rows where `success == True`, use `p=0.7`.
     - For rows where `success == False`, use `p=0.15`.
  2. Add a `steps_to_completion` column to the `runs` DataFrame: calculate this as `loop_count * np.random.randint(2, 5, size=len(runs))`.
  3. Modify the connector events generator loop: add a boolean `outcome_confirmed` column (set to `True` for 80% of successful runs using `np.random.rand() < 0.8`).

#### [NEW] `data/otel_mock_generator.py`
- **Function:** `generate_otel_traces(profile, num_traces, output_path="data/mock_traces.jsonl")`
- **Logic:** Output a JSONL file where each line is a JSON object with: `trace_id` (uuid4), `span_id` (uuid4), `parent_span_id` (uuid4 or null), `capability_id` (string), `loop_iteration` (int), `tokens_used` (int). Ensure multi-span traces contain parent-child relationships.

#### [MODIFY] `ontology/exception_taxonomy.py`
- **Logic:** In the `CATEGORIES` dictionary, add the following exact entries:
  - `"loop_exhaustion"`: `{"owner": "engineering", "severity": "high", "hint": "Agent exceeded loop budget; inspect planning step for goal drift or tool-call hallucination."}`
  - `"quality_drift"`: `{"owner": "data_science", "severity": "high", "hint": "Steps-to-completion trending up; output quality degrading before users notice."}`
  - `"eval_regression"`: `{"owner": "data_science", "severity": "high", "hint": "Offline eval score dropped >10% from prior version; do not ship until re-evaluated."}`
  - `"outcome_confirmation_gap"`: `{"owner": "product", "severity": "medium", "hint": "Run succeeds but downstream write events not observed; agent may be producing orphaned artifacts."}`

#### [MODIFY] `core/workspace.py`
- **Function:** `build_workspace()`
- **Logic:**
  1. Compute `connector_capability_graph`: Perform `pd.merge(connector_events, runs, on='run_id')`. Then `groupby(['connector_id', 'capability_id'])` and aggregate using `.agg(call_count=('connector_event_id', 'count'), fail_count=('success', lambda x: (~x).sum()))`. Assign this to `Workspace.connector_capability_graph`.
  2. Initialize an empty `eval_results` DataFrame: `pd.DataFrame(columns=['capability_id', 'capability_version', 'eval_suite_id', 'score', 'evaluated_at'])` and attach to `Workspace`.

### Layer 2: Economics Engine

#### [NEW] `data/pricing_oracle.yaml`
- **Structure:**
  ```yaml
  models:
    gpt-4o:
      input_cost_per_1k: 0.005
      output_cost_per_1k: 0.015
    claude-3-5-sonnet:
      input_cost_per_1k: 0.003
      output_cost_per_1k: 0.015
  ```

#### [NEW] `analytics/economics.py`
- **Function:** `calculate_run_cost(runs_df, profile, pricing_oracle_path)`
- **Logic:**
  1. Parse YAML to find `unit_price` based on `profile['default_model']`.
  2. Compute `cache_credit = step_count * (input_cost * profile.get('cache_hit_rate', 0.5))`.
  3. Compute `run_cost_usd = (tokens_per_step * step_count * unit_price) - cache_credit`.
  4. Return updated `runs_df`.

#### [MODIFY] `analytics/agentic_profile.py`
- **Logic:** In `PRESETS`, add `billing_model: 'b2b_subscription'`, `max_loops_threshold: 8`, and `cache_hit_rate: 0.7` to the `assistant_heavy`, `workspace_crm`, and `ops_mission` dictionaries.

### Layer 3: Causal Engine

#### [NEW] `analytics/trend_engine.py`
- **Function:** `compute_trends(runs_df, date_col='run_date')`
- **Logic:**
  1. Aggregate runs by `capability_id` over trailing 7d, 14d, 28d windows.
  2. Calculate `slope_per_week` for `steps_to_completion` using simple difference or linear regression.
  3. Return a dictionary mapping `capability_id` to `{"metric": "steps_to_completion", "direction": "worsening"|"improving", "slope_per_week": float}`.

#### [MODIFY] `analytics/decisions.py`
- **Function:** `classify(workspace)`
- **Logic:**
  1. Import and call `trend_engine.compute_trends(workspace.runs)`.
  2. Rule addition: If `trend['direction'] == 'worsening'` and `trend['slope_per_week'] > 0.05`, append `"quality_drift"` to exceptions list.
  3. Rule addition: If `mean(loop_count) > profile['max_loops_threshold']`, append `"loop_exhaustion"` to exceptions list.

### Layer 4: Control Plane & UI

#### [NEW] `api/main.py`
- **Logic:** Create a FastAPI instance.
  ```python
  from fastapi import FastAPI
  app = FastAPI(title="ChurnOS Control Plane")

  @app.get("/v1/capability/{capability_id}/verdict")
  def get_verdict(capability_id: str):
      # Return a JSON stub matching GrowthDecisionRecord schema
      return {"record_id": "...", "subject": {"capability_id": capability_id}, "exceptions": []}
  ```

#### [NEW] `pages/24_Eval_Governance.py`
- **Logic:** Create Streamlit page. Load `ws.eval_results` (from `get_workspace_from_session()`). Display a line chart using `px.line(x='evaluated_at', y='score', color='capability_version')`.

#### [NEW] `pages/25_Capability_Experiment.py`
- **Logic:** Create Streamlit page. Add two select boxes to pick `control_version` and `variant_version`. Display a mock Bayesian outcome chart comparing `churn_happened` rates. Add a `st.button` to emit a `GrowthDecisionRecord` with the winning `experiment_id`.

#### [MODIFY] `app.py` & `assets/style.css`
- **Logic:**
  1. In `app.py`, update `st.navigation()` call: `pg = st.navigation(nav_structure, expanded=True)`.
  2. Update the `nav_structure` dict keys to use the shortened names from Section 6A (e.g. "Radar" instead of "Capability Risk Radar").
  3. In `style.css`, append `[data-testid="stSidebarNav"] span[data-testid="stIconMaterial"] { display: none !important; }` to hide the material icons/chevrons.

---

## 6. Visualization & Narrative Depth

The architecture now holds real analytical depth (topology, dual billing, loop economics, causal posteriors, eval drift, micro-churn). **Most of that depth never reaches the viewer today.** Decision pages are mostly: 1–2 KPI metrics → optional bar/line → a stack of Decision Cards. Recruiters and PMs leave with “nice cards,” not proof that churnOS thinks like Amplitude + ChartMogul for agents.

**Goal:** every non-obvious claim in the engine should have a **visual receipt** the viewer can read in under 10 seconds — without turning the app into a metrics dashboard.

### 6.1 What viewers see today (gap)

| Surface | What ships | What’s missing for depth |
| --- | --- | --- |
| Capability Risk Radar | Ranked Decision Cards | No “why this week” strip, no portfolio tornado, no cost waterfall on home |
| Activation & Habit | ✅ Cohort line + capability success chart + cards | Micro-churn decay curves still open |
| Trust & Approval | ✅ Timeline + trust-by-capability + cards | Fatigue threshold line optional polish |
| Run Economics | ✅ Loop hist + waterfall + billing toggle + cost bars | Dual-panel revenue overlay polish |
| Connector Blast Radius | ✅ Fail bars + blast scatter (uses graph table) | True bipartite network graph still open |
| Outcome Flywheel | Write-back + cards | No before/after retention sparkline on the record |
| Ontology pages | Tables / gloss | No schema → record → exception storyboard |
| (planned) Topology / Causal / Eval | — | Risk of shipping as “more pages of cards” |

### 6.2 Design principles (how depth becomes legible)

1. **One claim → one visual receipt.** Every GDR exception category maps to a named chart or diagram. If `loop_exhaustion` fires, the card expands to a loop-budget histogram — not another paragraph.
2. **Progressive disclosure, magazine order.** First viewport: verdict + cost of leaving live. Second: evidence strip (sparklines). Third: expandable deep dive (posterior, topology, token stack). Never dump PyMC traces above the fold.
3. **Dual encoding.** Color for verdict severity; position/size for dollars or probability. Viewer who skims color still gets ranking; viewer who digs gets proof.
4. **Same visual grammar across pages.** Shared components in `ui/viz/` so Run Economics and Radar don’t invent two chart styles. Reuse `apply_plotly_theme` + magazine CSS variables.
5. **Honesty in the chart.** Associational claims use dashed lines / “association” captions; causal claims (with `experiment_id`) use solid CI bands. Methodology lives *on* the figure, not only in `page_help`.
6. **Story > gallery.** Prefer one composed figure that answers “what should I do?” over five unrelated Plotly charts.

### 6.3 Visual vocabulary (map depth → chart)

| Depth (from architecture) | Viewer question | Visualization | Where it lives |
| --- | --- | --- | --- |
| **Agentic Health Composite** | Who is at risk? | **Red/Yellow/Green composite score** (Cost + TTFV + Trust + Depth) | Radar home |
| **Portfolio ranking** | What matters this week? | Horizontal **tornado / cost-of-leaving-live bar** by capability; optional small multiples of verdict badges | Radar home |
| **Exception composition** | Why is this capability flagged? | **Stacked evidence strip** on Decision Card: category chips sized by `$ impact` | `ui/decision_card.py` |
| **Micro-churn / habit** | Is delegation dying? | **Decay curve**: weekly invocations per seat×capability vs cohort p50 band | Activation; card expand |
| **Activation First-Win** | Why ~40% revenue retention? | **Activation Funnel + TTFV Histogram**: Sign-up → Paid → First Verified Success | Activation |
| **Trust / approval** | Are humans rejecting the agent? | **Dual-axis timeline**: trust incidents + dismiss rate; fatigue threshold line | Trust page |
| **Catastrophic shocks** | What caused permanent churn?| **Event Log Overlay**: Severe agent failures mapped against NPS/churn spikes | Trust page |
| **Run economics / loops** | Where do dollars go? | **Waterfall**: tokens → loop steps → cache credit → net `run_cost_usd`; billing-model toggle redraws revenue side | Run Economics |
| **Hidden Run Complexity** | Where did it loop? | **Gantt Chart Timeline**: Tool calls, models, and cumulative $ burned per session | Run Economics / Expand |
| **Jevons Paradox** | Did cheaper tokens save $?| **Elasticity Scatter**: Unit token price vs. total token volume | Run Economics |
| **Dual billing** | Sub vs usage story? | **Small-multiples / toggle**: same cost stack, two revenue overlays (ARPU margin vs $/run) | Run Economics + Profile |
| **Connector blast radius** | What else breaks? | **Bipartite or hierarchical graph**: connector → capabilities; node size = dependent runs; edge color = fail rate | Connector page |
| **Integration Moat** | How easy to rip out? | **Integration Depth Score** bar chart per account | Connector page |
| **Agent topology / lineage** | Who passed bad data? | **Trace DAG** (Plotly or networkx→Plotly): parent→child spans; failed node highlighted; blame path emphasized | New Topology section / card expand |
| **Causal attribution** | Is this real or coincidence? | **Forest plot / posterior density** of churn effect by capability; shade if `experiment_id` missing | Causal / Radar expand |
| **Cold-start** | Why low confidence? | **Confidence thermometer** + “nearest neighbor” capability chips | Decision Card meta |
| **Eval governance** | Did quality regress? | **Version ladder**: eval score by `capability_version` with −10% ship gate line | Eval Governance page |
| **Quality / steps drift** | Is the agent getting worse? | **Control chart**: `steps_per_successful_task` with 7/14/28d window + 1.5σ bands | Eval / Activation |
| **Outcome flywheel** | Did the decision help? | **Before/after sparkline** on card after write-back: retention Δ + churn flag | Flywheel + card |
| **Trend / windows** | Getting better or worse? | **Slope badge** (↑↓) + mini sparkline of primary guardrail on every card | Cross-cutting |
| **Control plane** | What would the API return? | **Live verdict panel** (Streamlit): JSON response for `GET /verdict` next to the human card — proves machine API | Radar / Record Inspector |

### 6.4 Decision Card v2 — the primary depth carrier

Cards are the product’s editorial unit. Upgrade them so depth travels *with* the decision, not only on adjacent pages.

```
┌─────────────────────────────────────────────────────────┐
│ DESTRUCTIVE                          slope ↓ · 14d      │
│ CAP-042 · inbox_triage                                  │
│ 3 exceptions · loop_exhaustion, trust_break             │
│                                                         │
│  [spark: cost] [spark: loops] [spark: habit]            │  ← evidence strip
│                                                         │
│  $48,200  Cost of leaving live                          │
│  ▓▓▓▓▓▓▓▓░░░░  Confidence 0.72 (cold-start blended)     │
│                                                         │
│  ▼ Evidence (expand)                                    │
│     · Loop budget hist · Topology blame path            │
│     · Token waterfall · Posterior (if causal on)        │
│  ▼ Decision / override                                  │
└─────────────────────────────────────────────────────────┘
```

**Implementation notes:**
- Sparklines: precompute per-capability series in `analytics/decisions.py` or `analytics/trend_engine.py`; pass as `record["viz"]` stub so Streamlit doesn’t re-aggregate on every expand.
- Expand panels: `st.expander` wired to reusable `ui/viz/*` helpers (one module per chart family).
- Keep print/screenshot readability: sparklines must remain legible at ~120px width (IBM Plex Mono ticks, magazine accent).

### 6.5 Page-level compositions (not dashboards)

Each DECISIONS page should read as **one editorial composition**:

| Page | Composition (top → bottom) |
| --- | --- |
| **Radar** | Masthead → **Agentic Health Composite Scoreboard** → “This week’s burn” portfolio tornado → top 5 cards with evidence strips → optional topology thumbnail for #1 |
| **Activation & Habit** | Activation funnel + TTFV hist → Habit vs activation cohort → **micro-churn small multiples** (3 worst capabilities) → filtered cards |
| **Trust** | Catastrophic event timeline → Incident timeline → dismiss/approve mix → cards |
| **Run Economics** | Billing-model toggle as first control → dual-panel cost/revenue → Jevons elasticity chart → loop waterfall / Agent Gantt for selected capability → cards |
| **Connector** | Dependency graph (primary visual) → Integration depth score distribution → fail-rate bars as secondary → cards |
| **Eval Governance** | Version ladder + ship gate → regression table → cards |
| **Capability Experiment** | Experiment readout (Bayesian) → GDR with `experiment_id` badge → outcome write-back |
| **Record Inspector** | Raw JSON + rendered card + “visual receipts” attached to this record only |

Avoid KPI walls. If a metric isn’t named in the masthead deck or in a card exception, it doesn’t need a `st.metric` row.

### 6.6 Communicating uncertainty & honesty visually

Depth without credibility is noise. Encode methodology in the visuals:

| Claim type | Visual treatment |
| --- | --- |
| Synthetic / teaching estimate | Caption chip: `SYNTHETIC`; muted ink |
| Associational harm (no experiment) | Dashed CI / “association only” annotation |
| Causal (has `experiment_id`) | Solid interval; `EXPERIMENT` chip |
| Cold-start / low N | Confidence bar capped; grey “prior” segment |
| Billing-model counterfactual | Explicit toggle label: “Viewing as B2B subscription” |

These chips should appear on charts **and** Decision Cards so a screenshot carries the disclaimer.

### 6.7 Proposed UI artifacts

| Artifact | Role |
| --- | --- |
| [NEW] `ui/viz/sparklines.py` | Capability evidence strip (cost, loops, habit, trust) |
| [NEW] `ui/viz/activation.py` | Activation Funnel and TTFV histograms |
| [NEW] `ui/viz/economics_charts.py`| Jevons Elasticity chart, Agent Gantt timeline |
| [NEW] `ui/viz/health_composite.py`| Agentic Health composite score and color-coding |
| [NEW] `ui/viz/tornado.py` | Portfolio cost-of-leaving-live ranking |
| [NEW] `ui/viz/waterfall.py` | Token / loop / cache economics stack |
| [NEW] `ui/viz/topology.py` | Agent DAG + connector bipartite graph |
| [NEW] `ui/viz/posterior.py` | PyMC / forest plot helpers (P3) |
| [NEW] `ui/viz/decay.py` | Micro-churn delegation curves |
| [MODIFY] `ui/decision_card.py` | Evidence strip + expand panels; consume `record["viz"]` |
| [MODIFY] `ui/explain.py` | Surface explainers for new viz (“How to read this graph”) |
| [MODIFY] each DECISIONS page | Replace metric-only tops with compositions in §6.5 |

### 6.8 Phasing visualizations with the roadmap

| Phase | Viz work (ship with engine work, not after) |
| --- | --- |
| **P1** | Connector dependency graph; loop histogram on Run Economics; topology thumbnail from mock OTEL |
| **P2** | Token/loop waterfall; dual-billing toggle redraw; Radar tornado |
| **P3** | Decay curves; control charts; posterior/forest plots; eval version ladder; Decision Card evidence strip |
| **P4** | Verdict API live panel; landing-page hero that shows a *real* composed screenshot of Radar + card expand (not abstract gradients) |

**Rule:** no analytics module merges without its visual receipt in the same PR (or an explicit “viz follow-up” issue linked from the plan).

### 6.9 Success criteria for communication (viewer tests)

Manual checks — if these fail, the depth is still trapped in code:

1. A new viewer can answer “which capability would you throttle and why?” from Radar alone in **&lt; 60s** without opening Concepts.
2. Expanding one Decision Card shows **≥ 2** chart receipts that match its exception categories.
3. Toggling `billing_model` visibly changes the economics figure and at least one verdict/rationale string.
4. Connector page shows a **graph**, not only a fail-rate bar.
5. Any causal-looking chart without `experiment_id` is visually marked as association-only.
6. Screenshot of one card is intelligible in a portfolio README without extra captioning.

---

## 6A. Sidebar Navigation UX (fix before adding more pages)

The multipage sidebar is fighting the magazine UI. Two Streamlit defaults make it worse:

1. **Section chevrons (`expand_more`)** — `st.navigation({section: [pages…]})` renders collapsible section headers with a Material Icons chevron. With our styled headers (`stNavSectionHeader`), that glyph overlaps or clips long titles (“Connector Blast Radius”, “Trust & Approval Health”) and reads as broken Chrome, not editorial chrome.
2. **Nav collapse / “View more”** — With ~25 pages plus the brand block above the nav in `app.py`, Streamlit may collapse the list. That second expand control stacks with section chevrons and hides DECISIONS / LEGACY items behind another click.

Visual issues on top of that: sepia paper sidebar is fine, but the brand blurb is tall; page titles wrap awkwardly; LEGACY dumps ten reference pages into the primary path; active-state left border fights Streamlit’s default padding.

### 6A.1 Design goals

- Nav should feel like a **table of contents**, not Streamlit’s default accordion.
- Primary path visible without hunting: Profile → Radar → 4 DECISIONS surfaces → Flywheel.
- LEGACY reachable but visually demoted (collapsed by default or behind a single entry).
- No Material Icons glyphs clipping labels; no “View X more” in the OSS demo.
- Section labels stay as quiet kickers (mono, uppercase) — they are not click targets that steal attention.

### 6A.2 Recommended fixes (ordered by leverage)

#### A. Kill the broken expand affordances (P0 — CSS + one API flag)

```python
# app.py
pg = st.navigation(nav_structure, expanded=True)  # no "View more" collapse
```

```css
/* assets/style.css — hide section chevrons; keep section label text */
[data-testid="stNavSectionHeader"] svg,
[data-testid="stSidebarNav"] [data-testid="stIconMaterial"],
[data-testid="stSidebarNav"] span[data-testid="stIconMaterial"],
[data-testid="stSidebarNav"] .material-icons,
[data-testid="stSidebarNav"] button[kind] svg {
  display: none !important;
}

/* Prevent label truncation under where the chevron sat */
[data-testid="stNavSectionHeader"] {
  display: flex !important;
  align-items: center !important;
  gap: 0 !important;
  overflow: visible !important;
  white-space: nowrap !important;
}

[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] a span {
  white-space: normal !important;
  line-height: 1.25 !important;
  overflow: visible !important;
  text-overflow: unset !important;
  padding-right: 0.5rem !important;
}
```

If Streamlit still toggles sections on header click after hiding the icon, add `pointer-events: none` on the header (labels stay readable; pages remain clickable). Prefer keeping sections **always expanded** for CORE / DECISIONS / EXPERIMENT / ONTOLOGY.

#### B. Shorten titles + shrink chrome (P0)

Long titles are what the chevron clips. Rename for the nav (page mastheads can stay long):

| Current nav title | Suggested short title |
| --- | --- |
| Capability Risk Radar | Radar |
| Agentic Product Profile | Product Profile |
| Concepts & Playbook | Concepts |
| System Architecture | Architecture |
| Trust & Approval Health | Trust & Approval |
| Connector Blast Radius | Connectors |
| Seat Retention & Churn | Seat Retention |
| Seat Unit Economics | Seat Economics |
| Experimentation Court | Experiments |
| Business Model (legacy) | Business Model |
| Lifecycle & NSM (legacy) | Lifecycle |

Also shorten the sidebar brand block in `app.py`: keep kicker + one line (“Profile → Generate → Radar”). Move the longer synthetic disclaimer into Radar’s `synthetic_notice()` only — it currently burns vertical space above every page’s nav.

#### C. Demote LEGACY so the TOC fits (P0 / P1)

Do **not** list 10 legacy pages as peers of Activation & Habit.

Options (pick one):

1. **Preferred:** Single nav entry `Legacy (reference)` → `pages/99_Legacy_Index.py` that links/embeds the old suite with `ui/legacy_banner.py`. Removes ~10 sidebar rows.
2. **Alternative:** Keep LEGACY section but default it collapsed via CSS/`localStorage` override, or move those files out of `st.navigation` and load only when `?legacy=1`.
3. **Avoid:** `position="top"` for everything — top nav with 25 pages is worse for this product.

After demotion, sidebar target: **≤ 14 visible links** (CORE 4 + DECISIONS 4–6 + EXPERIMENT 2 + ONTOLOGY 3 + Legacy 1).

#### D. Visual polish (P1 — still CSS, magazine-aligned)

```css
[data-testid="stSidebar"] {
  min-width: 16.5rem !important; /* room for two-line titles without crush */
}

[data-testid="stSidebarNav"] a {
  border-radius: 0 !important; /* match mag cards: no soft pills */
  margin: 0.1rem 0.35rem !important;
  border-left: 2px solid transparent !important;
}

[data-testid="stSidebarNav"] [aria-current="page"] {
  border-left-color: var(--mag-accent) !important;
  background: var(--mag-paper-elevated) !important;
}

/* Quiet section rhythm: more air before CORE/DECISIONS, less between links */
[data-testid="stNavSectionHeader"] {
  margin-top: 1.25rem !important;
  opacity: 0.9;
}
```

Optional: add `icon=` on `st.Page` sparingly (Radar, Profile only) — or **no icons** to avoid another Material glyph layer competing with expand_more. Prefer zero icons until chevrons are gone.

#### E. Structural option if CSS keeps losing (P2)

If Streamlit upgrades keep reintroducing chevrons, replace grouped `st.navigation(dict)` with a **flat** page list + custom section labels injected as non-clickable markdown between groups (hacky) — or a thin custom sidebar TOC using `st.page_link` under `position="hidden"` navigation. Only pursue if A–D fail; grouped nav is still the right API.

### 6A.3 Proposed file changes

| Change | Purpose |
| --- | --- |
| [MODIFY] `app.py` | `st.navigation(..., expanded=True)`; shorten titles; slim brand blurb; collapse LEGACY to one index page |
| [MODIFY] `assets/style.css` | Hide nav Material Icons / chevrons; fix overflow; spacing; min-width |
| [NEW] `pages/99_Legacy_Index.py` | Single entry point for legacy suite |
| [MODIFY] README nav table | Match short titles; Legacy as one row |

### 6A.4 Acceptance checks

1. No `expand_more` / chevron glyph visible in the sidebar on Chrome or Firefox.
2. No “View more” / “View less” control under the page list.
3. Full titles of primary DECISIONS links readable without hover truncation.
4. Fresh visitor reaches Product Profile + Radar + Run Economics with ≤ 1 scroll in the sidebar.
5. LEGACY does not occupy more than one nav row on the default path.

---

## 7. Success Metrics

| Metric | Target |
| --- | --- |
| Evaluate pipeline latency (generate → GDR) | < 30s for default profile (~800 seats) |
| `run_cost_usd` accuracy vs. oracle | Within 2% on fixture set |
| False-positive throttle rate | < 5% on synthetic harm A/B |
| GDR schema validation pass rate | 100% in CI |
| Demo offline mode | Zero network deps with `data_source=synthetic` |
| Loop-cost model: cache credit accuracy | Within 5% of Anthropic/OpenAI pricing page |
| Viewer comprehension (manual) | Answer “throttle which capability & why?” from Radar in &lt; 60s (§6.9) |
| Card depth coverage | Expanded Decision Card shows ≥2 visual receipts matching its exceptions |

---

## 8. Heuristic Thresholds to Replace

| Rule | Location | Replacement |
| --- | --- | --- |
| `run_count < 5` → `capability_dead` | classify() | Cold-start policy + adoption prior |
| `success_rate < activation_rate * 0.6` | classify() | Control chart vs. seat cohort baseline |
| `harm_score > 0.08` | classify() | PyMC posterior + experiment gate |
| `dismiss_rate > approval_fatigue_rate` | classify() | Bayesian approval queue model |
| `trust_rate > trust_incident_rate * 1.5` | classify() | Poisson exceedance |
| `run_cost_mean > run_cost_per_success * 2` | classify() | Loop-cost engine + oracle-priced runs |
| *(new)* `loop_count > max_loops` | classify() | Loop exhaustion exception |
| *(new)* `steps_to_completion drift > 1.5σ` | classify() | Quality drift exception |
| *(new)* `eval_score delta < -10%` | classify() | Eval regression exception |

---

## Appendix: Architecture Decisions Log

| # | Decision | Resolution |
| --- | --- | --- |
| 1 | Pricing model | **Simulate both** — `b2b_subscription` and `usage_based` via `profile.billing_model` |
| 2 | Ontology evolution | **Opportunistic** — expand schema only when real trace shapes demand it |
| 3 | Storage backend | **JSONL/pandas** for now; DuckDB migration path documented |
| 4 | Real-time vs. batch | **Run-as-you-go** — no streaming pipeline in OSS toolkit |
| 5 | Loop modeling | **Bimodal generator** — geometric(p=0.7) normal, geometric(p=0.15) failure |
| 6 | Quality signal | **Steps-to-completion** primary; `outcome_confirmed` connector event secondary |
| 7 | Eval governance | **Activate in P3** — `eval_results` table + `eval_drift` classifier |
| 8 | Connector graph | **First-class derived table** in Workspace — computed at build time |
| 9 | Experiment bridge | **`capability_version` as subject** — new `pages/25_Capability_Experiment.py` |
| 10 | Trend / time-series | **Trailing windows** (7d/14d/28d) with slope + severity escalation |
| 11 | Landing page | **Shipped pre-P4** — portfolio design language; shipped-features-only copy; P4 may add API receipts |
| 12 | Visualization depth | **Visual receipts required** — every exception category maps to a named chart; Decision Card v2 carries evidence strips; see §6 |
| 13 | Sidebar nav | **Fix in P0** — hide `expand_more` chevrons, `expanded=True`, shorten titles, collapse LEGACY to one index; see §6A |

---

## 9. Implementation Progress Log

Living log of what has been shipped against this plan. Newest first.

### 2026-08-04 — Landing page (`index.html`)

- Full rewrite using portfolio design language (DM Sans/Mono, teal tokens, zero-radius cards)
- Agentic OSS toolkit copy: Profile → Radar → GDR, four decision surfaces, ontology callout, honesty note
- CTAs: GitHub, live demo (`churnos.xblavania.workers.dev`), local `streamlit run` instructions
- Gap 7 / ADR 11 updated: landing ships pre-P4; control-plane receipts deferred

### 2026-08-04 — P1 core + P2 economics start

**P0 (complete earlier same session)**
- Sidebar: `st.navigation(..., expanded=True)`, short titles, slim brand, LEGACY demoted via `visibility="hidden"` + `pages/99_Legacy_Index.py`
- CSS: hide Material chevrons / overflow fixes (`assets/style.css`)

**P1 — shipped**
| Item | Artifact |
| --- | --- |
| Bimodal `loop_count` / `steps_to_completion` / tokens on runs | `data/agentic_generator.py` (`DATA_VERSION=2.1-agentic`) |
| `outcome_confirmed` on connector events | same |
| Taxonomy: `loop_exhaustion`, `quality_drift`, `eval_regression`, `outcome_confirmation_gap` | `ontology/exception_taxonomy.py` |
| Lexicon metrics for steps/loops/confirmation/eval/trend | `metrics/lexicon.yaml` + resolvers in `analytics/metrics.py` |
| `connector_capability_graph` + seeded `eval_results` | `core/workspace.py` |
| Mock OTEL JSONL generator | `data/otel_mock_generator.py` |
| Trend engine (7/14/28d slope) | `analytics/trend_engine.py` |
| Classifiers for loop / quality drift / confirmation gap | `analytics/decisions.py` |
| Decision-page charts (activation, trust, economics, connectors) | `ui/viz/decisions_charts.py` + DECISIONS pages |

**P2 — started**
| Item | Artifact |
| --- | --- |
| Pricing oracle YAML | `data/pricing_oracle.yaml` |
| Token/loop cost + cache credit + dual billing margins | `analytics/economics.py` |
| Profile fields: `billing_model`, `default_model`, `max_loops_threshold`, `cache_hit_rate` | `analytics/agentic_profile.py` |
| New preset `api_metered` (`usage_based`) | same |
| Workspace build re-prices runs via oracle | `core/workspace.py` `price_runs=True` |
| Run Economics: billing toggle, loop hist, cost waterfall | `pages/17_Run_Economics.py` |

**Tests**
- `tests/unit/test_economics.py`
- `tests/unit/test_p1_agentic_extensions.py`
- Existing `test_decisions.py` / `test_agentic_generator.py` green

**Still open (next)**
- [ ] `data/ingestion.py` — parse OTEL mock → warehouse (beyond JSONL write)
- [ ] Radar portfolio tornado viz + Agentic Health composite scoreboard
- [ ] Decision Card v2 evidence strips
- [ ] Expanded Agentic Visuals (Jevons Elasticity, Agent Gantt timeline, TTFV Funnel, Integration Depth)
- [ ] `pages/24_Eval_Governance.py` + eval_regression classifier wiring to `eval_results`
- [ ] `pages/25_Capability_Experiment.py`
- [ ] `analytics/causal_agent.py` (PyMC)
- [ ] `analytics/micro_churn.py`
- [ ] FastAPI control plane (`api/main.py`)
- [ ] PII scrubber pipeline (metadata-only already in OTEL mock; no real prompt bodies yet)

### How to verify locally

```bash
# Unit slice for this tranche
pytest tests/unit/test_economics.py tests/unit/test_p1_agentic_extensions.py tests/unit/test_decisions.py -q

# UI: regenerate workspace (Product Profile) then open Run Economics / Connectors / Activation
streamlit run app.py
```

