# churnOS · Decision-grade analytics for agentic software systems

_Portfolio-ready **simulated decision OS** for agentic software companies (Lindy-class assistants, Dench-class workspaces, Invice-class ops agents)._

---

## What this repo is

churnOS is a **working model of how an agentic product company should decide** which capabilities (skills, automations, agent tools) to ship, throttle, rollback, or kill — priced by the cost of leaving them live, with outcomes written back so the loop can improve.

It is **not** another metrics dashboard. Dashboards show *what happened*. churnOS emits an auditable **GrowthDecisionRecord** — a shared object for humans, agents, and partners — that answers *what to do next*.

Configure an **Agentic Product Profile**, generate a synthetic agentic warehouse, and explore ranked decisions on the **Capability Risk Radar**.

> **Evolution:** churnOS began as a causal growth & operations intelligence simulator (B2C / SaaS / marketplace / ecomm). The agentic rebuild reframes the product around **ontology as IP**. Prior modules live under **LEGACY** nav — nothing was deleted.

---

## Why it exists

Growth and product operators shipping agentic systems face a specific fracture:

- Spreadsheets and BI tools hold partial truths — CAC here, churn there, experiment readouts stranded elsewhere.
- Capabilities ship continuously (prompts, tools, connectors, workflows) while **weekly decisions die in dashboards**: which lever to pull, what a cohort’s churn is costing, which capabilities harm retention.
- Agents that should self-improve need a **stable product language** — not ad-hoc chart labels — or the loop never closes.

**Ontology as IP** is the answer this repo demonstrates:

| Layer | Artifact | Job |
| --- | --- | --- |
| **Taxonomy** | `ontology/exception_taxonomy.py` | Named exceptions, owners, playbook hints |
| **Semantics** | `ontology/*/semantics.yaml` | Gloss **and** governing rules (thresholds → verdict → action) |
| **Schema** | `ontology/shared/*.schema.json` | Contract for `GrowthDecisionRecord` |
| **Rules engine** | `ontology/decision_rules.py` | Reads YAML at emit time — policy without code changes |

Same pattern as project-theta’s decision-record recipe, adapted for **capability shipping in agentic systems** — not B2C churn dashboards.

Synthetic generators keep every screen reproducible offline. Hypothesis-backed tests safeguard numerical contracts. See [`docs/honesty.md`](docs/honesty.md) for synthetic / associational limits.

Perfect for recruiters evaluating **analytics + product sense + engineering hygiene** — and for teams prototyping how agentic products should govern capability shipping at scale.

Canonical docs live **here**. [`pages/6_README.py`](pages/6_README.py) renders this file — edit `README.md` only.

Further reading: **[Methodology](docs/methodology.md)** · **[Honesty & limits](docs/honesty.md)** · **[Ontology package](ontology/README.md)** · **[Interview showcase plan](docs/interview_showcase_plan.md)**

---

## How it works (one sentence)

Pick a product profile → generate synthetic agent runs → classify exceptions using YAML thresholds → map to a verdict and action from semantics → emit a **GrowthDecisionRecord** → rank it on the Radar → write retention / churn outcomes back.

```text
Profile (ontology switch)
   → Warehouse (seats · capabilities · runs · approvals · connectors)
   → Classify (exceptions from thresholds)
   → YAML rules (verdict → recommended action)     ← edit policy here
   → GrowthDecisionRecord
   → Capability Risk Radar (Decision Cards)
   → Outcome Flywheel ──(write-back)──→ same record
```

### Weekly decision loop

1. **Profile** — Pick a preset (`assistant_heavy`, `workspace_crm`, `ops_mission`, …). That choice switches the ontology vertical and synthetic priors.
2. **Generate** — Build the agentic warehouse from those priors.
3. **Radar** — Rank capabilities by `cost_of_leaving_live_usd`.
4. **Decide** — Review exceptions and recommended action; override if needed.
5. **Close loop** — Outcome Flywheel writes `retention_delta_*` and `churn_happened` onto the same record.

### Why YAML matters

Verdicts and recommended actions are **not hardcoded in Python**. The profile’s vertical loads `semantics.yaml`; that file governs policy. Same exception signal, different product context → different action:

| Exception | Vertical (profile) | Verdict | Recommended action |
| --- | --- | --- | --- |
| `capability_harm` | `agent_runtime` (`assistant_heavy`) | destructive | **rollback** |
| `capability_harm` | `capability_lifecycle` (`workspace_crm`) | destructive | **throttle** |

Edit sample values in YAML → regenerate workspace → Radar cards update. No code change required.

What you tune in `semantics.yaml`:

- **`classification.thresholds`** — when does `classify()` fire? (e.g. `harm_score_min: 0.08`)
- **`decision.verdict_rules`** — first match wins (categories → verdict)
- **`decision.action_map`** — verdict → `recommended_action` + `requires_review`

### GrowthDecisionRecord (the stable object)

| Field | Job |
| --- | --- |
| `exceptions[]` | What broke (category + cost + owner + playbook) |
| `economics` | `cost_of_leaving_live_usd` (primary metric) |
| `decision.verdict` | `healthy` · `leaking` · `destructive` · … |
| `decision.recommended_action` / `final_action` | `ship` · `throttle` · `rollback` · `kill` · … (+ human override) |
| `outcome` | Retention Δ + churn write-back |

Schemas: [`ontology/shared/`](ontology/shared/). Validate:

```bash
python3 -m ontology --examples
```

### Ontology verticals

| Vertical | Role |
| --- | --- |
| `capability_lifecycle` | Ship / throttle / kill capabilities |
| `agent_runtime` | Runtime trust, loops, cost (stricter; destructive → rollback) |
| `orchestration` | Multi-agent handoffs (sample rules) |
| `eval_governance` | Eval gate / regression (sample rules) |

First two are day-1 active (profiles switch between them). See [`ontology/README.md`](ontology/README.md).

### What it measures (and what it doesn’t)

**Yes — a model of what should be measured:** seat activation, weekly delegation habit, trust incidents, approval fatigue, cost per successful run, connector blast radius, capability-level harm associations and economic pricing.

**Not yet — live instrumentation:** numbers are **synthetic** until real run/approval/connector events plug into the same warehouse schema. `capability_harm` is **associational** unless an `experiment_id` is on the record. Outcome write-backs are portfolio demos, not production causal attribution.

See [`docs/honesty.md`](docs/honesty.md).

---

## Highlights

### Agentic rebuild (primary)

| Area | What churnOS showcases |
| --- | --- |
| **Ontology IP** | Taxonomy → semantics → JSON Schema → `GrowthDecisionRecord` |
| **YAML-governed policy** | Verdicts & actions from `semantics.yaml` via `decision_rules.py` |
| **Capability Risk Radar** | Ranked decisions with magazine-style Decision Cards |
| **Agentic warehouse** | Seats, capabilities, runs, approvals, connectors |
| **Decision surfaces** | Activation, trust, run economics, connector blast radius |
| **Outcome flywheel** | Retention Δ + churn labels on records (JSONL store) |
| **Profile presets** | `assistant_heavy`, `workspace_crm`, `ops_mission`, … |
| **In-app explainers** | `ui/explain.py` — how it works, measurement honesty, glossary |

### Legacy simulator (reference)

| Area | What churnOS showcases |
| --- | --- |
| **Executive calibration** | Causal waterfall, sensitivity grid, simulated cohort segmentation |
| **Retention & churn** | Survival modelling, churn drivers with interpretability caveat, triangles |
| **Product analytics** | Activation windows, behavioural stickiness analogue, instrumentation sandbox |
| **Experimentation hub** | Shared workspace, user assignment, SRM, z-test + Bayesian, governed guardrails |
| **Market intelligence** | Take-rate gymnastics, liquidity, seller cohort behaviour |
| **Attribution rigour** | PyMC Bayesian MMM with diminishing returns scaffolding |

---

## Navigation

Aligned with sidebar groups in [`app.py`](app.py):

| Group | Modules |
| --- | --- |
| **START** | Product Profile |
| **DECIDE** | Radar · Activation & Habit · Trust & Approval · Run Economics · Connectors |
| **LEARN** | Experiments · Outcome Flywheel |
| **Reference** (collapsed) | Concepts · Architecture · Semantics · Taxonomy · Record Inspector |
| **Legacy** (collapsed) | Legacy index → Business Model, Retention, Unit Economics, marketplace, ecomm, MMM, CRO (see [`legacy/README.md`](legacy/README.md)) |

---

## Getting started

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for private-collaborator setup, fast vs full tests, and the 5-minute agentic path.

**Interview / hiring:** [`docs/interview_kit.md`](docs/interview_kit.md) · [`docs/genai_for_math.md`](docs/genai_for_math.md)

```bash
cd churnOS
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt          # core app (Profile → Radar)
pip install -r requirements-dev.txt      # pytest + hypothesis
streamlit run app.py                     # browse http://localhost:8501
pytest tests/ -m "not slow" --hypothesis-profile=dev   # fast test path
```

Optional MMM (Attribution page): `pip install -r requirements-mmm.txt`

1. Open **Product Profile** → pick preset → **Generate workspace**
2. **Capability Risk Radar** shows ranked records
3. Drill into DECIDE surfaces or override on Record Inspector / Radar
4. **Outcome Flywheel** — write synthetic outcomes back to close the loop

**Policy playground:** change `agent_runtime` destructive action from `rollback` to `shadow` in [`ontology/agent_runtime/semantics.yaml`](ontology/agent_runtime/semantics.yaml), regenerate with `assistant_heavy`, watch Radar cards update.

> PyMC-heavy attribution (LEGACY) needs `pip install -r requirements-mmm.txt` — then use **Run Bayesian Sampler** on the Attribution page. Keep local seeds stable when recording demos.

Continuous integration: [.github/workflows/ci.yml](.github/workflows/ci.yml) (includes ontology example validation).

---

## Repository anatomy

```
churnOS/
├── app.py                               # Capability Risk Radar home + grouped navigation
├── core/
│   └── workspace.py                     # Unified warehouse (agentic + legacy tables)
├── ontology/                            # Decision-grade IP
│   ├── exception_taxonomy.py            # Taxonomy
│   ├── decision_rules.py                # YAML → verdict / action
│   ├── semantics.py · validate.py · store.py
│   ├── shared/*.schema.json             # GrowthDecisionRecord contract
│   └── */semantics.yaml                 # capability_lifecycle, agent_runtime, …
├── analytics/
│   ├── agentic_profile.py               # Profile presets (ontology switch)
│   ├── decisions.py                     # Classify → rank → price → emit records
│   ├── causal_model.py · churn.py · retention.py
│   ├── conversion.py · experimentation.py
│   ├── ecommerce.py · marketplace.py · pricing.py
│   └── attribution.py                   # Bayesian MMM (PyMC) — LEGACY
├── data/
│   ├── agentic_generator.py             # Synthetic agentic warehouse
│   └── generator.py                     # Legacy customers, funnel, behavioural events
├── metrics/
│   └── lexicon.yaml                     # Governed KPI definitions (agentic + legacy)
├── ui/
│   ├── magazine.py                      # Editorial chrome (masthead, Plotly theme)
│   ├── decision_card.py                 # GrowthDecisionRecord card renderer
│   ├── explain.py                       # In-app help / glossary / honesty notices
│   └── legacy_banner.py                 # LEGACY page banner
├── pages/
│   ├── 00_Agentic_Product_Profile.py
│   ├── 15_Activation_Habit.py … 23_Record_Inspector.py   # Agentic surfaces
│   └── 0_Business_Model.py … 14_Conversion_Forecast.py   # LEGACY reference
├── docs/methodology.md · honesty.md
├── assets/style.css                     # Sepia editorial light theme
└── tests/                               # Unit + integration + ontology validation
```

### Data flow (legacy warehouse)

```text
customers + downstream generators
        │
 ┌──────┴───────────┬──────────────────┐
 funnel events      transactional rows   marketing panel
 └──────▲───────────▴──────────────────┘
        │
 behavioural `product_events` (Instrumentation sandbox)
        │
 analytics stack (pandas / sklearn / scipy / pymc pathways)
        │
 Streamlit canvases (+ Plotly overlays)
```

`generate_all_data()` returns **`product_events`** alongside customers, funnel, marketplace, buyers, marketing.

Suggested CSV schema for imports:

```text
product_events.csv
- customer_id (string)
- event_ts (ISO-8601 timestamp)
- event_name (enumerated strings: view_item, add_to_cart, …)
- props_json (optional JSON blob)
```

---

## Tooling

| Tag | Packages |
| --- | --- |
| App shell | Streamlit · Plotly |
| Core analytics | pandas · NumPy · SciPy · scikit-learn · lifelines |
| Ontology | jsonschema · PyYAML |
| Attribution lane (LEGACY) | pymc · arviz |
| Quality | pytest · Hypothesis |

---

## License

Copyright (c) 2026 churnOS. All rights reserved. Not licensed for redistribution.
