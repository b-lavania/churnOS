# Churn and Marketplace Analytics

A comprehensive Streamlit application for ecommerce and marketplace operators — acting as a **live interactive business calculator** covering **churn analysis**, **unit-economics retention**, **conversion optimization**, and **marketplace pricing**.

## Overview

This application provides a powerful simulation suite with interactive dashboards. It's built for founders, growth teams, and operators who need to model "what-if" scenarios. The app generates thousands of rows of synthetic customer, transaction, and funnel data on the fly based on the highly granular **Simulation Controls** provided on every page. Use it to understand how macro changes to your business levers (like CAC, refunds, or commissions) cascade down to your ultimate bottom line.

## Core Features & Simulation Levers

Every page includes a **Simulation Controls** section right below the header allowing you to instantly regenerate the underlying data based on advanced business parameters:

| Page | Description & Simulation Controls |
|------|-----------------------------------|
| **Churn Analysis** | Cohort survival, driver ID, revenue churn vs logo churn. **Controls:** Base Churn Multiplier, Premium Mix, **Subscribe & Save %** (flattens survival curves by dropping base churn). |
| **Retention** | Cohort heatmaps, Day-N retention, and True Margin CLV. **Controls:** AOV, Discount Freq, **Refund Rate %**, **COGS %**, **Blended CAC**. Includes a live *LTV:CAC Ratio* tracking profitability! |
| **Conversion Optimization** | Funnel visualization from Visit to Purchase, drop-off analysis. **Controls:** N Sessions, Checkout Dropoff, Mobile Share, and a **Free Shipping** toggle to model volume vs. margin tradeoffs. |
| **Pricing Analytics** | Take-rate analysis, elasticity simulation, buyer vs seller split. **Controls:** Seller Volume, Take Rate Multiplier, Fee Splits, and a **Fixed Per-Transaction Fee ($)** to model margin expansion. |
| **Knowledge Base** | Metric definitions, formulas, industry benchmarks, and actionable playbooks. |
| **README** | This documentation rendered within the app. |

## Architecture

```
churn-analysis/
|
|-- app.py                              # Main entry point, page config, landing page
|-- requirements.txt                    # Python dependencies
|
|-- assets/
|   |-- style.css                       # Premium dark theme (glassmorphism, Inter font)
|
|-- data/
|   |-- __init__.py
|   |-- generator.py                    # Synthetic dataset generation
|       |-- generate_customers()        #   5,000 customers with segment-dependent churn
|       |-- generate_transactions()     #   ~50,000 transaction records
|       |-- generate_funnel_events()    #   30,000 funnel sessions with device/source
|       |-- generate_marketplace_pricing()  # 500 sellers with tiers and fee structures
|
|-- analytics/
|   |-- __init__.py
|   |-- churn.py                        # Churn rate, cohort churn, survival analysis, RF drivers
|   |-- retention.py                    # Cohort retention matrix, CLV, Day-N retention, curves
|   |-- conversion.py                   # Funnel summary, drop-off, segment conversion, A/B test
|   |-- pricing.py                      # Take-rate, price elasticity, commission tiers, fee split
|
|-- pages/
    |-- 1_Churn_Analysis.py             # Churn dashboards with data input
    |-- 2_Retention.py                  # Retention dashboards with data input
    |-- 3_Conversion_Optimization.py    # Conversion dashboards with data input
    |-- 4_Pricing_Analytics.py          # Pricing dashboards with data input
    |-- 5_Knowledge_Base.py             # Metric definitions and playbooks
    |-- 6_README.py                     # This README rendered in the app
```

### Data Flow

```
                    +------------------+
                    |   Data Input     |
                    | (CSV Upload or   |
                    |  Synthetic Data) |
                    +--------+---------+
                             |
                    +--------v---------+
                    |  data/generator   |
                    |  (Synthetic Data) |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v-----+  +-----v------+
     | analytics/ |  | analytics/ |  | analytics/ |
     | churn.py   |  | retention  |  | conversion |
     +--------+---+  +------+-----+  +-----+------+
              |              |              |
              +--------------+--------------+
                             |
                    +--------v---------+
                    |   Streamlit UI   |
                    |  (pages/*.py)    |
                    +------------------+
```

### Analytics Module Details

**churn.py**
- `compute_churn_rate()` — Overall and grouped churn rates
- `compute_cohort_churn()` — Churn rate by signup month cohort
- `revenue_vs_logo_churn()` — Compare customer count churn vs revenue churn
- `churn_drivers()` — Random Forest feature importance for churn prediction
- `survival_analysis()` — Kaplan-Meier survival curves by segment

**retention.py**
- `cohort_retention_matrix()` — Triangular retention heatmap data
- `clv_estimate()` — CLV = AOV x Frequency x Lifespan
- `retention_curve()` — Retention percentage by month, grouped by channel or segment
- `day_n_retention()` — D1, D7, D14, D30, D60, D90 retention metrics

**conversion.py**
- `funnel_summary()` — Session counts and conversion rates at each funnel step
- `drop_off_analysis()` — Identify biggest funnel drop-off points
- `segment_conversion()` — Conversion rate by device or traffic source
- `ab_test_significance()` — Two-proportion Z-test with confidence intervals

**pricing.py**
- `take_rate_analysis()` — GMV, net revenue, effective take rate by category
- `price_elasticity_sim()` — Demand and revenue curves given price elasticity
- `commission_tier_model()` — Revenue breakdown by commission tier
- `fee_split_scenario()` — Model buyer vs seller fee allocation impact

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
cd churn-analysis
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Using Your Own Data

Each analytics page has a **Data Input** expander at the top where you can:
1. **Upload a CSV** matching the expected schema (column names shown in the UI)
2. **Adjust parameters** to regenerate synthetic data with different settings

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web application framework |
| pandas | Data manipulation |
| numpy | Numerical computation |
| plotly | Interactive charts |
| scipy | Statistical tests (A/B testing) |
| scikit-learn | Random Forest for churn drivers |
| lifelines | Kaplan-Meier survival analysis |

## License

MIT
