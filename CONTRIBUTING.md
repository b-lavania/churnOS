# Contributing to churnOS

**Private collaborator access only.** Copyright (c) 2026 churnOS. All rights reserved. Not licensed for redistribution, public forks, or commercial use without permission.

---

## Setup

Requires Python **3.12** (see [`.python-version`](.python-version)).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest + hypothesis (for tests)
```

**Optional — Marketing Mix Modeling (LEGACY Attribution page):**

```bash
pip install -r requirements-mmm.txt
```

Core install is enough for **Product Profile → generate workspace → Radar**.

---

## Run the app

```bash
streamlit run app.py
```

### 5-minute agentic path

1. **Product Profile** — pick a preset (e.g. `assistant_heavy`) → **Generate workspace**
2. **Radar** — ranked GrowthDecisionRecords (capabilities + accounts)
3. **Semantics Console** — optional policy overlay → reclassify
4. **Outcome Flywheel** — write synthetic outcomes back to close the loop

No Business Model setup required for the agentic path.

---

## Tests

**Fast path (recommended while iterating):**

```bash
pytest tests/ -m "not slow" --hypothesis-profile=dev
```

**Full suite (CI mirrors this, may take several minutes):**

```bash
pytest tests/ ontology/tests/ --hypothesis-profile=dev
```

Validate ontology examples:

```bash
python3 -m ontology --examples
```

---

## Honesty & synthetic data

All warehouse data is **synthetic** unless you plug in real telemetry. Read [`docs/honesty.md`](docs/honesty.md) before claiming causal lift or production readiness in demos.

---

## Math / analytics PRs

Follow [`docs/math/README.md`](docs/math/README.md): pure function → tests → Math Lab → DECIDE/LEARN hook.

Teaching modules wired in UI but **without dedicated tests yet** (PRs welcome):

- `analytics/bandits.py`
- `analytics/queueing.py`
- `analytics/pareto.py`
- `analytics/stochastic_economics.py`
- `analytics/flag_segments.py`

---

## Where to edit policy without code

- `ontology/*/semantics.yaml` — thresholds, verdict → action maps
- **Semantics Console** — session overlay (not written to disk)
