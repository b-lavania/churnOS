# churnOS

Figuring out how agentic products should handle churn, retention, and monetization.

---

## How this started

The first version of this was a bunch of spreadsheets. Retention curves, churn cohort breakdowns, attribution models for a couple of marketplaces and ecomm stores I was studying. I was trying to answer the same question everyone asks: *why are people leaving, and what can we actually do about it?*

Those spreadsheets turned into a Python project. I built out a causal waterfall, survival models, experimentation scaffolding, even a full Bayesian MMM pipeline with PyMC. It worked, in the sense that the math was sound, but it was still fundamentally about customers and transactions. Traditional SaaS/ecomm retention.

Then I started paying attention to agentic products (AI assistants, CRM copilots, ops agents) and realized the retention problem is completely different there: you're not retaining customers in the old sense, instead you're shipping features (skills, automations, agent tools).

So, the question becomes: is this capability helping or hurting? Is it worth the inference cost? Should we throttle it, roll it back, or kill it entirely? The old spreadsheet models didn't have a place for that; I rebuilt the whole thing around capabilities instead of customers and that's ***churnOS***.

---

## What it actually does

You pick a product profile (what kind of agentic product are you?), generate a synthetic warehouse of seats, capabilities, agent runs, approvals, and connectors, and then the engine classifies exceptions, prices the cost of leaving things as they are, and gives you ranked decisions on a Radar.

```text
Profile (ontology switch)
   > Warehouse (seats, capabilities, runs, approvals, connectors)
   > Classify (exceptions from thresholds)
   > YAML rules (verdict > recommended action)     < edit policy here
   > GrowthDecisionRecord
   > Capability Risk Radar (Decision Cards)
   > Outcome Flywheel (write-back onto the same record)
```

The loop, step by step:

1. **Profile** Pick a preset (`assistant_heavy`, `workspace_crm`, `ops_mission`, `marketplace_agentic`, etc.). That switches the ontology vertical and the synthetic priors.
2. **Generate** Build the agentic warehouse from those priors.
3. **Radar** Rank capabilities by `cost_of_leaving_live_usd`.
4. **Decide** Review exceptions and the recommended action. Override if you disagree.
5. **Close loop** Outcome Flywheel writes `retention_delta` and `churn_happened` back onto the same record.

---

## Why YAML matters

This is the part I'm most stubborn about. Verdicts and recommended actions are **not hardcoded in Python**. The profile's vertical loads a `semantics.yaml` file, and that file governs policy. Same exception signal, different product context, different action:


| Exception         | Vertical (profile)                       | Verdict     | Recommended action |
| ----------------- | ---------------------------------------- | ----------- | ------------------ |
| `capability_harm` | `agent_runtime` (`assistant_heavy`)      | destructive | **rollback**       |
| `capability_harm` | `capability_lifecycle` (`workspace_crm`) | destructive | **throttle**       |


I wanted the rules to live in config, not buried in Python, so anyone could change what "destructive" means without touching code. Edit sample values in YAML, regenerate workspace, Radar cards update. No deploy needed.

What you tune in `semantics.yaml`:

- `classification.thresholds` when does `classify()` fire? (e.g. `harm_score_min: 0.08`)
- `decision.verdict_rules` first match wins (categories to verdict)
- `decision.action_map` verdict to `recommended_action` + `requires_review`

The ontology has a few verticals: `capability_lifecycle`, `agent_runtime`, `marketplace_commerce`, `orchestration`, `eval_governance`. The first three are the active ones. Details in `[ontology/README.md](ontology/README.md)`.

---

## What's here and what's not

**The main thing** is the agentic rebuild. Taxonomy of exceptions, YAML semantics, JSON Schema contract for the `GrowthDecisionRecord`, ranked Radar with Decision Cards, and an outcome flywheel that closes the loop. Profile presets for different product shapes. Marketplace Radar for agent-assisted GMV economics. Tier 2 math (confidence sequences, drift detection, empirical Bayes shrinkage, token VaR).

**The legacy simulator pages** are still here, under the Legacy nav. Retention, unit economics, marketplace liquidity, CRO, all of it. I didn't delete anything. Those pages use the old customer/transaction model and they still work. They're reference.

**MMM and multi-touch attribution.** I spent a lot of time on these. The Bayesian MMM pipeline with PyMC, adstock curves, diminishing returns, the whole thing. But honestly, it's not the main event here. I left it in for anyone who wants to explore it (`pip install -r requirements-mmm.txt`, then the Attribution page), but I'm not going to pretend it's polished or that it's the point of this repo.

**Everything is synthetic.** All the numbers come from authored generators, not production telemetry. The math is real, the data is not. I tried to be upfront about this everywhere (there's a synthetic notice on every page, and `[docs/honesty.md](docs/honesty.md)` spells out exactly what's real vs simulated). If you plug real event data into the same warehouse schema, the analytics work the same way. I just haven't done that yet.

**Harm scores are associational**, not causal, unless there's an `experiment_id` on the record. I want to be careful about that distinction.

---

## Getting started

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for collaborator setup, fast vs full tests, and the 5-minute agentic walkthrough.

```bash
cd churnOS
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt          # core app
pip install -r requirements-dev.txt      # pytest + hypothesis
streamlit run app.py                     # http://localhost:8501
pytest tests/ -m "not slow" --hypothesis-profile=dev
```

1. Open **Product Profile**, pick a preset, hit **Generate workspace**
2. **Capability Risk Radar** shows ranked records
3. Drill into DECIDE surfaces or override on Record Inspector
4. **Outcome Flywheel** writes synthetic outcomes back to close the loop

If you want to play with policy: change the `agent_runtime` destructive action from `rollback` to `shadow` in `[ontology/agent_runtime/semantics.yaml](ontology/agent_runtime/semantics.yaml)`, regenerate with `assistant_heavy`, and watch the Radar cards update.

CI: [.github/workflows/ci.yml](.github/workflows/ci.yml)

Further reading: [Methodology](docs/methodology.md), [Honesty and limits](docs/honesty.md), [Ontology package](ontology/README.md), [Ideas](docs/ideas/README.md)

---

## Repository layout

```
churnOS/
├── app.py                          # Radar home + grouped navigation
├── core/workspace.py               # Unified warehouse (agentic + legacy)
├── ontology/
│   ├── exception_taxonomy.py       # Named exceptions, owners, playbook hints
│   ├── decision_rules.py           # YAML to verdict/action
│   ├── shared/*.schema.json        # GrowthDecisionRecord contract
│   └── */semantics.yaml            # per-vertical policy
├── analytics/
│   ├── agentic_profile.py          # Profile presets
│   ├── decisions.py                # Classify, rank, price, emit
│   ├── marketplace_economics.py    # Agent-assisted GMV margin
│   ├── inference/                  # CS, empirical Bayes, SPRT, binomial
│   ├── drift.py                    # KL/JS mix drift, CUSUM
│   ├── token_risk.py               # VaR/CVaR, price shock
│   └── attribution.py             # Bayesian MMM (legacy, PyMC)
├── data/
│   ├── agentic_generator.py        # Synthetic agentic warehouse
│   └── generator.py                # Legacy customers/funnel/events
├── metrics/lexicon.yaml            # Governed KPI definitions
├── ui/
│   ├── magazine.py                 # Editorial chrome
│   ├── decision_card.py            # GDR card renderer
│   └── explain.py                  # In-app help, glossary, honesty
├── pages/                          # Streamlit pages (agentic + legacy)
├── docs/                           # Methodology, honesty, interview kit
├── assets/style.css
└── tests/                          # Unit + integration + ontology validation
```

---

## Tooling


| What                 | Packages                                      |
| -------------------- | --------------------------------------------- |
| App shell            | Streamlit, Plotly                             |
| Core analytics       | pandas, NumPy, SciPy, scikit-learn, lifelines |
| Ontology             | jsonschema, PyYAML                            |
| Attribution (legacy) | pymc, arviz                                   |
| Quality              | pytest, Hypothesis                            |


---

## License

Copyright (c) 2026 churnOS. All rights reserved. Not licensed for redistribution.