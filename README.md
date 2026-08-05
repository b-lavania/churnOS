# churnOS · Decision-grade analytics for agentic software systems

_Portfolio-ready **simulated decision OS** for agentic software companies (Lindy-class assistants, Dench-class workspaces, Invice-class ops agents)._

Configure an **Agentic Product Profile**, generate a synthetic agentic warehouse, and explore ranked **GrowthDecisionRecords** — which capabilities to ship, throttle, or kill — priced by **cost of leaving live**, with retention and churn outcome write-back.

> **Evolution:** churnOS began as a causal growth & operations intelligence simulator (B2C / SaaS / marketplace / ecomm). The agentic rebuild reframes the product around **ontology as IP** and **decision-grade analytics** for continuously shipping agentic systems. Prior modules are preserved under **LEGACY** nav for reference — nothing was deleted.

---

## Portfolio story & intent

Growth leaders face the same fracture: spreadsheets hold partial truths — CAC in one workbook, churn in another, experiment readouts stranded across tooling — while dashboards show *what happened* but rarely *what to do next*.

**Agentic churnOS** closes that gap with a single calibrated simulator where:

- **Ontology** (taxonomy → semantics → JSON Schema) defines a stable, auditable object — the `GrowthDecisionRecord` — that partners, agents, and dashboards can share.
- **Capability Risk Radar** ranks weekly decisions that usually die in a dashboard: which growth lever to pull, what a cohort's churn is costing, and which product capabilities are negatively correlated with retention.
- **Outcome flywheel** writes retention Δ and churn labels back to records, closing the loop for self-improving agentic workflows.

Synthetic generators keep every screen reproducible offline. Hypothesis-backed tests safeguard core numerical contracts. See [`docs/honesty.md`](docs/honesty.md) for synthetic / associational limits.

Perfect for recruiters evaluating **analytics + product sense + engineering hygiene** — and for teams prototyping how agentic products should govern capability shipping at scale.

Canonical documentation lives **here**. [`pages/6_README.py`](pages/6_README.py) renders this file verbatim — edit `README.md` only.

Further reading: **[Methodology](docs/methodology.md)** · **[Honesty & limits](docs/honesty.md)** · **[Ontology package](ontology/README.md)**

---

## Highlights

### Agentic rebuild (primary)

| Area | What churnOS showcases |
| --- | --- |
| **Ontology IP** | Taxonomy → semantics → JSON Schema → `GrowthDecisionRecord` |
| **Capability Risk Radar** | Ranked decisions with magazine-style Decision Cards |
| **Agentic warehouse** | Seats, capabilities, runs, approvals, connectors |
| **Decision surfaces** | Activation, trust, run economics, connector blast radius |
| **Outcome flywheel** | Retention Δ + churn labels on records (JSONL store) |
| **Profile presets** | `assistant_heavy`, `workspace_crm`, `ops_mission` ontology switches |
| **In-app explainers** | `ui/explain.py` — how it works, measurement honesty, field glossary |

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

## How it works

```text
Agentic Product Profile (ontology switch + priors)
        ↓
data/agentic_generator.py → Workspace (seats, capabilities, runs, approvals, connectors)
        ↓
analytics/decisions.py → classify exceptions → rank → price → emit GrowthDecisionRecord
        ↓
Capability Risk Radar (Decision Cards) + ontology/store.py (JSONL persistence)
        ↓
Outcome Flywheel → write retention_delta + churn_happened back to records
```

### Weekly decision loop

1. **Profile** — Pick a preset (`assistant_heavy`, `workspace_crm`, `ops_mission`) on **Agentic Product Profile**.
2. **Generate** — Build a synthetic agentic warehouse from profile priors.
3. **Radar** — Home screen ranks capabilities by `cost_of_leaving_live_usd`.
4. **Decide** — Review exceptions, recommended action (`ship` / `throttle` / `kill`), override if needed.
5. **Close loop** — Outcome Flywheel writes post-decision metrics to the same record.

### GrowthDecisionRecord (the stable object)

Inspired by project-theta's `DecisionRecord` pattern, adapted for agentic product management:

| Field | Purpose |
| --- | --- |
| `exceptions[]` | Classified problems (`activation_leak`, `capability_harm`, `run_cost_blowout`, …) |
| `economics.primary_metric_usd` | Primary economic metric — cost of leaving live (label in `primary_metric_label`) |
| `decision.verdict` | `healthy` · `leaking` · `destructive` · … (from YAML rules) |
| `decision.recommended_action` / `final_action` | `ship` · `throttle` · `kill` · … (+ operator override) |
| `outcome` | `retention_delta_*`, `churn_happened` — written back after action |

**Governing decisions from data:** verdicts, recommended actions, and classification thresholds live in
[`ontology/*/semantics.yaml`](ontology/) — edit sample values, regenerate workspace, Radar updates.
See [`ontology/README.md`](ontology/README.md). Example: `agent_runtime` maps `destructive` → `rollback`;
`capability_lifecycle` maps the same verdict → `throttle`.

Schemas live in [`ontology/shared/`](ontology/shared/). Validate examples:

```bash
python3 -m ontology.validate --examples
```

### What it measures (and what it doesn't)

**Yes — a model of what should be measured:**

- Seat activation rate, weekly delegation habit
- Trust incident rate, approval fatigue
- Cost per successful run, connector blast radius
- Capability-level harm associations and economic pricing

**Not yet — live instrumentation:**

- Numbers are **synthetic** until you connect real run/approval/connector events.
- `capability_harm` is **associational** unless an `experiment_id` is present on the record.
- Outcome write-backs are portfolio demonstrations, not production causal attribution.

See in-app **Measurement honesty** expander on the Radar, or [`docs/honesty.md`](docs/honesty.md).

---

## Getting started

```bash
cd churnOS
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt          # aligns with [.python-version](.python-version)
streamlit run app.py                     # browse http://localhost:8501
pytest tests/ --hypothesis-profile=dev    # mirrors CI pacing
```

1. Open **Agentic Product Profile** → pick preset → **Generate workspace**
2. Home **Capability Risk Radar** shows ranked records
3. Drill into **DECISIONS** surfaces or override on Record Inspector / Radar
4. **Outcome Flywheel** — write synthetic outcomes back to close the loop

> PyMC-heavy attribution (LEGACY) stays interactive via explicit **Run Bayesian Sampler** — keep local seeds stable when recording demos.

Continuous integration: [.github/workflows/ci.yml](.github/workflows/ci.yml) (includes ontology example validation).

---

## Repository anatomy

```
churnOS/
├── app.py                               # Capability Risk Radar home + grouped navigation
├── core/
│   └── workspace.py                     # Unified warehouse (agentic + legacy tables)
├── ontology/                            # Decision-grade IP (taxonomy, semantics, schemas)
│   ├── exception_taxonomy.py
│   ├── semantics.py · validate.py · store.py
│   ├── shared/*.schema.json
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
├── docs/methodology.md
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
| Ontology | jsonschema |
| Attribution lane (LEGACY) | pymc · arviz |
| Quality | pytest · Hypothesis |

---

## License

Distributed under **MIT** — see [`LICENSE`](LICENSE).
