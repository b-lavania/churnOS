# GenAI for mathematics (honest contract)

churnOS has **no LLM SDK** in the analytics path. This document explains how genAI-for-math works across the portfolio without overclaiming.

## The split

| Layer | Role | Example |
| --- | --- | --- |
| **Perception / language** | LLM extracts structure from messy inputs | [Moovez Vision Agent](https://github.com/moovezceo/Moovez-Vision-Agent) — photo → line items |
| **Deterministic math** | Auditable formulas, inference, simulation | Moovez quote calculator; churnOS `analytics/` |
| **Policy / ontology** | YAML thresholds, verdict → action maps | `ontology/*/semantics.yaml` → `GrowthDecisionRecord` |

**Rule:** LLMs never own `$` math inside churnOS. Optional future: LLM *explains* a GDR using semantics — non-authoritative narration only.

## Moovez (live production proof)

1. User uploads move photo
2. Gemini perceives items and conditions
3. Deterministic pricing engine computes quote bands
4. Human reviews before send

Interview line: *"We use genAI where perception helps; economics stay in tested code."*

## churnOS (interview hero)

1. Product Profile sets ontology + `math_mode`
2. Synthetic warehouse feeds survival, experimentation, economics
3. Semantics YAML + Decision Card encode policy
4. Rigorous mode surfaces calibration, conformal bands, knapsack, bandits

Interview line: *"Same DecisionRecord pattern as physical ops (project-theta) and diligence (project-epsilon), with statistical engines you can audit."*

## What we do not claim

- Synthetic warehouse ≠ production telemetry
- Teaching bandits ≠ live traffic allocation without governance
- Uplift without `experiment_id` ≠ causal proof (see [`honesty.md`](honesty.md))

## Related

- [`interview_showcase_plan.md`](interview_showcase_plan.md) — Tier 1 build checklist
- [`math/README.md`](math/README.md) — contributor contract
- [`interview_kit.md`](interview_kit.md) — 5-minute demo script
