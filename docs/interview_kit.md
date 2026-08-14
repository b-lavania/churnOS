# Interview kit

**Goal:** rehearsed 5-minute loop proving genAI-for-math (Moovez) + shipped decision OS (churnOS).

## Before the call

```bash
git clone https://github.com/b-lavania/churn-analysis.git churnOS
cd churnOS
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
streamlit run app.py
```

Preset: `assistant_heavy` · `math_mode: rigorous` on Product Profile.

## Talk track (5 min)

### 0:00–1:30 — Moovez (genAI for math)

- Open [Moovez Vision Agent demo](https://visionagent.streamlit.app/) or local clone
- Photo → Gemini items → **deterministic** quote math
- Emphasize: *no LLM in pricing*

### 1:30–4:30 — churnOS (decision OS)

1. **Product Profile** → Generate workspace
2. **Radar** — sort by `cost_of_leaving_live_usd` with conformal band on account cards
3. **Semantics Console** — tweak `p_churn_30d_min` → reclassify
4. **Outcome Flywheel** — write synthetic outcome (closes loop)
5. If asked *"how do you know?"* → **Lab · Calibration** or **Lab · Decision Curves**

**Marketplace preset (Q4):** `marketplace_agentic` → **Marketplace Radar** for agent-assisted GMV margin. **Lab · Drift** for mix-shift; Version Compare for confidence sequences.

Knapsack line (Radar banner or Run Economics): *"With N HITL slots this week, review these accounts first."*

### 4:30–5:00 — Siblings

- **project-theta** — same DecisionRecord pattern in physical ops
- **project-epsilon** — diligence KG; not expanded for this demo

## Honesty limits (say out loud)

- All warehouse data is synthetic unless you plug real telemetry
- Bandits and knapsack are teaching/governance surfaces, not live rollout
- Attribution is permutation importance on hazard — audit trail, not causal SHAP

## Deep-dive files (if interviewer opens the repo)

| Path | Shows |
| --- | --- |
| `ontology/growth_decision_record.schema.json` | Decision object contract |
| `analytics/survival.py` | Fitted hazard + calibration |
| `analytics/stochastic_economics.py` | Conformal bands |
| `analytics/decision_curves.py` | Net-benefit threshold |
| `analytics/knapsack.py` | Intervention selection under capacity |
| `analytics/bandits.py` | YAML-governed traffic + regret |
| `tests/unit/test_interview_math.py` | Ground-truth recovery |
| `tests/unit/test_marketplace_economics.py` | Marketplace margin economics |
| `analytics/marketplace_economics.py` | Agent-mediated GMV margin |
| `pages/35_Marketplace_Radar.py` | Marketplace DECIDE surface |

## License / access

Private collaborator repo — all rights reserved. See [`CONTRIBUTING.md`](../CONTRIBUTING.md).
