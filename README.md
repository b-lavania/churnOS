# churnOS · Causal growth & operations intelligence

_Portfolio-ready **simulated Product Analytics OS** for experimentation-minded analytics leaders._
Configure a business once, then explore behaviour, run statistically literate experiments, and translate wins into unit economics—on a **single synthetic event warehouse** (Mixpanel/Heap/Amplitude-style spine, not disconnected dashboards).

---

## Portfolio story & intent

Growth leaders face the same fracture: spreadsheets hold partial truths—CAC in one workbook, churn in another,
experiment readouts stranded across tooling, while churnOS folds those narratives into **one calibrated simulator**
so you can reason about trade-offs coherently. Synthetic generators keep every screen reproducible offline,
Hypothesis-backed tests safeguard core numerical contracts, while methodology notes call out causal limits.

Perfect for recruiters evaluating **analytics + product sense + engineering hygiene**—not just chart polish.

Suggested capture set for README viewers (swap in files under `assets/` as you capture them):

- [`assets/mockup.png`](assets/mockup.png)
- Planned: Executive Summary KPI stack
- Planned: Lifecycle & NSM Proxies heatmap ribbon
- Planned: Bayesian MMM posterior snapshot
- Screen recording suggestion: `<2‑minute Loom showcasing Business Model → Executive Summary → Product Lifecycle>`
  (swap in URL when published)

Canonical documentation lives **here**. [`pages/6_README.py`](pages/6_README.py) simply renders this file verbatim—edit `README.md` only.

Further reading: **[Methodology appendix](docs/methodology.md)** (assumptions, associational pitfalls, experimentation guardrails).

---

## Highlights

| Area | What churnOS showcases |
| --- | --- |
| **Executive calibration** | Causal waterfall, sensitivity grid, simulated cohort segmentation |
| **Retention & churn** | Survival modelling, churn drivers with interpretability caveat, triangles |
| **Product analytics** | Activation windows, behavioural stickiness analogue, instrumentation sandbox |
| **Experimentation hub** | Shared workspace, user assignment, SRM, z-test + Bayesian, governed guardrails, program registry |
| **Market intelligence** | Take-rate gymnastics, liquidity, seller cohort behaviour |
| **Attribution rigour** | PyMC Bayesian MMM with diminishing returns scaffolding |

Simulation controls regenerate synthetic facts per surface; alternatively upload schemas noted in-context.

---

## Navigation map (aligned with sidebar)

| Sidebar group | Modules |
| --- | --- |
| **CORE** | Business Model • Executive Summary • Concepts & Playbook • System Architecture (this README rendered in-app) |
| **PRODUCT** | Lifecycle & NSM Proxies (`pages/11_Product_Lifecycle.py`) — includes event-first journeys |
| **B2C / SaaS** | Retention & Churn • Unit Economics |
| **EXPERIMENT** | Experimentation Hub • CRO Program (legacy) • Revenue Leakage • Conversion Forecast |
| **ECOMMERCE** | RFM & Inventory |
| **MARKETPLACES** | Pricing Analytics • Seller Analytics • Marketplace Liquidity |
| **ATTRIBUTION** | Attribution & MMM |

[`app.py`](app.py) configures this layout via grouped `streamlit.navigation`.

---

## Repository anatomy

```
churnOS/
├── app.py                               # Landing + grouped navigation bootstrap
├── core/
│   └── workspace.py                     # Unified synthetic warehouse + experiment tables
├── metrics/
│   └── lexicon.yaml                     # Governed KPI definitions
├── requirements.txt                     # Pip dependencies (+ testing stack)
├── .python-version                      # Target interpreter (validated locally on 3.12.x)
├── LICENSE                              # MIT
├── docs/
│   └── methodology.md                   # Inference guardrails / synthetic caveats
├── assets/
│   └── style.css                        # Neon glass theme + typography
├── data/
│   └── generator.py                     # Synthetic customers, funnel, behavioural events…
├── analytics/
│   ├── causal_model.py
│   ├── churn.py · retention.py
│   ├── conversion.py
│   ├── ecommerce.py · marketplace.py · pricing.py
│   ├── attribution.py                  # Bayesian MMM (PyMC)
│   └── product_metrics.py               # Lifecycle, stickiness analogue, experimentation helpers
└── pages/
    ├── 0_Business_Model.py
    ├── 1_Retention_Churn.py
    ├── 2_Unit_Economics.py
    ├── 3_Conversion.py
    ├── 4_Marketplace.py
    ├── 5_Marketplace_Analytics.py
    ├── 6_README.py
    ├── 7_Concepts.py
    ├── 8_ECommerce_Analytics.py
    ├── 9_Marketplace_Liquidity.py
    ├── 10_Attribution_MMM.py
    ├── 11_Product_Lifecycle.py       # Acquisition / Activation / Monetisation scoreboard
    └── ui/journey.py                   # Breadcrumb + data-contract chrome
```

### Data flow cheat sheet

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

`generate_all_data()` now returns **`product_events`** alongside customers, funnel, marketplace, buyers, marketing.

Suggested CSV schema additions for imports:

```text
product_events.csv
- customer_id (string)
- event_ts (ISO-8601 timestamp)
- event_name (enumerated strings: view_item, add_to_cart, …)
- props_json (optional JSON blob)
```

---

## Getting started / reproducibility

```bash
cd churnOS
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt          # aligns with [.python-version](.python-version)
streamlit run app.py                     # browse http://localhost:8501
pytest tests/ --hypothesis-profile=dev    # mirrors CI pacing
```

> PyMC-heavy attribution stays interactive via explicit **Run Bayesian Sampler**—keep local seeds stable when recording demos.

Continuous integration blueprint: [.github/workflows/ci.yml](.github/workflows/ci.yml)

---

## Tooling highlights

| Tag | Packages |
| --- | --- |
| App shell | Streamlit · Plotly |
| Core analytics | pandas · NumPy · SciPy · scikit-learn · lifelines |
| Attribution lane | pymc · arviz |
| Quality | pytest · Hypothesis |

---

## License

Distributed under **MIT**—see [`LICENSE`](LICENSE).
