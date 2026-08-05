# Rebuild Plan: Align churnOS with `docs/methodology.md`

**Date:** 2026-08-04  
**Source of truth for retention IP:** [`methodology.md`](methodology.md)  
**Source of truth for Decision OS / control plane:** [`implementation_plan.md`](implementation_plan.md)

---

## 1. Verdict

`methodology.md` is no longer a short honesty appendix. It is a full **Agentic Retention System** build plan: Account→Run→Outcome→Revenue joins, five core metrics, a churn taxonomy, and Phase 0–3 go-to-market.

**churnOS today is a different product:** a synthetic **GrowthDecisionRecord Decision OS** (Profile → warehouse → heuristic exceptions → Radar). It overlaps methodology in spirit (agent cost, trust, activation, outcomes) but **does not implement the methodology data model or metric dictionary**.

| Layer | methodology.md | churnOS today |
| --- | --- | --- |
| Center of gravity | **Data model + four joins** | **Ontology + GDR decisions** |
| Grain | Account / EndUser / Session / AgentRun / Span / Outcome | Workspace / Seat / Capability / Run / Connector |
| Activation | First **verified autonomous outcome** ≤14d | Seeded `is_activated` boolean |
| Habit signal | **Delegation ratio** (agent vs manual) WoW | Seat `weekly_delegation` boolean |
| Autonomy | Agent-resolved / (agent + HITL) | Approvals dismiss rate only |
| Economics | Cost per **successful outcome** + **contribution-margin NRR** | $/successful **run** + seat margin proxy |
| Quality | **Outcome success drift** | Steps slope → `quality_drift` |
| Churn | Reason codes (`tourist`, `value_failure`, …) | Associational `capability_harm` + seat `is_churned` |
| Delivery | Weekly account health report + alerts | Decision Cards + Streamlit |
| Honesty | Phase 0 kill criteria / unverified flags | UI explainers (methodology no longer carries GDR caveats) |

**Strategy:** Do **not** throw away the Decision OS. **Rebuild the warehouse and metrics to match methodology**, then **emit GDRs from those metrics**. Ontology remains the decision layer; methodology becomes the measurement layer.

```
methodology data model + metrics  →  exception taxonomy / GDR  →  Radar + alerts
        (what happened)                    (what to do)           (who acts)
```

---

## 2. Keep / Rebuild / Drop

### Keep (still valuable)

- Ontology IP: taxonomy, semantics, GDR schema, Record Inspector
- Profile → Generate → Radar UX and magazine Decision Cards
- Dual billing simulation + pricing oracle (maps to seat vs usage pricing_model)
- Loop / token / connector blast-radius machinery (feeds cost-per-outcome)
- Trend engine scaffold (`analytics/trend_engine.py`)
- OTEL mock direction (batch ingest, no prompt bodies — matches methodology §3.4)
- OSS posture (toolkit, not churnOS SaaS billing)

### Rebuild (methodology requires it)

| Current | Rebuild to |
| --- | --- |
| `workspaces` / `seats` as primary org/user | `accounts` + `end_users` (+ keep seat as optional alias for B2B seat products) |
| Flat `runs` with `success` bool | `agent_runs` with status enum + `goal` + HITL fields + `outcome_id` |
| No first-class Outcome | `outcomes` table (`outcome_type`, `verified_by`, `outcome_value_usd`) |
| `outcome_confirmed` on connectors only | Outcome entity + verification path (deterministic / human / llm_judge) |
| `weekly_delegation` boolean | Weekly **delegation_ratio** time series per account (and capability) |
| Missing autonomy metric | **autonomy_ratio** from HITL vs agent-resolved outcomes |
| `$/successful run` as headline | **cost_per_successful_outcome** as headline; run cost remains COGS input |
| Seat margin only | **contribution_margin_nrr** cohort metric |
| `quality_drift` via steps only | **outcome_success_drift** WoW by outcome_type × agent_version × account |
| Churn = `is_churned` flag | Churn taxonomy reason codes on account |
| Activation page = first success proxy | Activation = days-to-first-**verified** outcome |

### Drop or demote

- Treating LEGACY funnel/CRO as part of the agentic story (already demoted — keep)
- Pretending `capability_harm` is causal without `experiment_id` (enforce in emit)
- README claim that methodology.md is the “associational honesty” doc — **split docs**: methodology = retention system; keep honesty in `docs/honesty.md` or restore a short appendix in methodology Part 8

---

## 3. Target architecture (reconciled)

```
+---------------------------+     +----------------------------+
|  Ingestion (batch)        |     |  Warehouse (methodology)   |
|  OTEL / Langfuse export   | --> |  Account, EndUser, Session |
|  Stripe / usage CSV       |     |  AgentRun, Span, Outcome   |
|  App DB outcomes          |     |  Subscription, UsageEvent  |
+---------------------------+     +----------------------------+
                                            |
                                            v
                                  +----------------------------+
                                  |  Metric dictionary         |
                                  |  activation, delegation,   |
                                  |  autonomy, $/outcome,      |
                                  |  CM-NRR, success drift     |
                                  +----------------------------+
                                            |
                                            v
                                  +----------------------------+
                                  |  Decision layer (keep)     |
                                  |  classify → GDR → Radar    |
                                  |  churn reason codes        |
                                  |  playbooks / alerts        |
                                  +----------------------------+
```

**Naming bridge (migration):**

| Methodology | churnOS v2.1 today | Action |
| --- | --- | --- |
| Account | `workspaces` (+ plan) | Rename/add `accounts`; map `tier`, `pricing_model` |
| EndUser | `seats` | Split: seat ≠ user; add `end_users`, keep seats for seat_based |
| Session | *(missing)* | Add `sessions` |
| AgentRun | `runs` | Extend schema; rename conceptually |
| Span | OTEL mock only | Persist `spans` / `trace_spans` in Workspace |
| Outcome | `outcome_confirmed` bool | First-class `outcomes` table |
| Subscription / UsageEvent | synthetic ARPU only | Add tables; generate synthetically first |

---

## 4. Metric dictionary → GDR mapping

| Methodology metric | Lexicon key (proposed) | Exception / decision trigger |
| --- | --- | --- |
| First verified outcome ≤14d | `activation_verified_14d` | `tourist` / `activation_leak` |
| Delegation ratio WoW | `delegation_ratio` | `habit_collapse`, churn `efficiency` / `value_failure` |
| Autonomy ratio WoW | `autonomy_ratio` | `approval_fatigue`, degradation vs edge-case growth |
| Cost per successful outcome | `cost_per_successful_outcome` | `run_cost_blowout`, churn `price` |
| Contribution-margin NRR | `contribution_margin_nrr` | `cac_ltv_contradiction` / margin-negative cohort |
| Outcome success drift | `outcome_success_drift` | `quality_drift`, churn `value_failure` |

Wire **churn reason codes** into taxonomy (new categories or `exception.metadata.churn_reason`):

`tourist` · `value_failure` · `efficiency` · `displacement` · `price` · `champion_departure` · `product_gap`

---

## 5. Phased build (churnOS-shaped, methodology-faithful)

OSS constraint: no dependency on “call 3 friends.” Phases below are **product engineering** phases that still honor methodology kill criteria as *validation gates when real data appears*.

### M0 — Doc & honesty reset (≤2 days)

1. Add Part 8 to methodology (or `docs/honesty.md`): synthetic limits, associational vs causal, teaching formulas.
2. Fix README link text: methodology = retention system IP; honesty = separate.
3. Update §0 of `implementation_plan.md` to point at this alignment plan.

**Exit:** One reader can tell “measurement model” from “decision OS” without confusion.

### M1 — Warehouse rebuild (synthetic-first) (1–2 weeks)

**Goal:** Implement methodology §3 entities in the generator + Workspace. Keep Streamlit demo offline.

1. Extend `data/agentic_generator.py` (or new `data/retention_generator.py`) to emit:
   - `accounts`, `end_users`, `sessions`, `agent_runs`, `spans`, `outcomes`, `subscriptions`, `usage_events`
2. Map Quotely-like and Lindy-like outcome type presets in Product Profile.
3. Preserve backward-compatible views (`seats`/`runs`) as thin adapters so existing pages don’t break day one.
4. Tests: FK integrity for the four joins; no prompt bodies in stored tables.

**Exit:** `build_workspace()` exposes all eight entity tables; four joins queryable in pandas.

### M2 — Metric dictionary (1–2 weeks)

1. Implement resolvers for the five core metrics + activation verified.
2. Rebuild Activation & Habit page around **verified outcome** + **delegation ratio** curves (not boolean habit).
3. Rebuild Run Economics around **$/successful outcome** + CM-NRR teaching chart; keep billing_model toggle.
4. Add Autonomy strip to Trust page (HITL vs resolved).
5. Emit missing classifiers: `habit_collapse`, `connector_fragility`, wire `eval_regression` from `eval_results`.

**Exit:** Lexicon + unit tests for each methodology metric on synthetic data with known ground truth.

### M3 — Churn taxonomy + account health Radar (1 week)

1. Account-level health scorecard: delegation trend, autonomy trend, $/outcome, success drift.
2. Churn risk list with reason codes (synthetic labels first).
3. Map scorecard rows → GDRs (one GDR per account *or* per capability — pick account for methodology fidelity; keep capability GDRs for Decision OS).
4. Playbook hints already in taxonomy → surface on cards.

**Exit:** Radar can answer methodology’s weekly report question: “which accounts are at risk and why?”

### M4 — Intervention loop (alerts as GDRs) (1 week)

Methodology Phase 2 → productized as **decision emissions**, not email SaaS:

| Alert rule | GDR action |
| --- | --- |
| Delegation ↓ >15% WoW | `throttle` / `experiment` + owner growth/CS |
| Autonomy ↓ >10% over 4w | `rollback` / eng owner |
| $/outcome > pricing margin | `hold` / finance |
| No verified outcome in 14d | `tourist` activation intervention |

**Exit:** Same rules produce stable GDRs in tests; Flywheel write-back uses outcome success, not only seat churn flag.

### M5 — Ingestion path (parallel after M1) (1–2 weeks)

1. `data/ingestion.py`: OTEL mock / Langfuse-shaped JSONL → AgentRun + Span.
2. Outcome import stub (CSV/JSON) for `verified_by`.
3. Stripe CSV stub → Subscription (optional; synthetic default).
4. Keep batch/run-as-you-go (methodology §3.4).

**Exit:** `data_source=otel` builds a Workspace that fills methodology metrics without the old flat generator alone.

### M6 — Later (from implementation_plan, still valid)

- Capability Experiment page + `experiment_id` on GDR (causal gate)
- Eval Governance page
- FastAPI verdict API
- Causal PyMC only *after* experiment_id path exists

---

## 6. Immediate code debt to fix while rebuilding

These undermine both products today — fix in M1/M2, don’t wait:

1. **`habit_collapse` / `connector_fragility` filtered on pages but never classified** → empty Decision sections.
2. **`experiment_id` never set on GDRs** → causal honesty unenforceable.
3. **`cac_ltv_contradiction` / `eval_regression` unused** despite taxonomy.
4. **README economics field name** (`cost_of_leaving_live_usd` vs `primary_metric_usd` + label).
5. **methodology.md vs honesty** documentation split.

---

## 7. What “rebuild” does *not* mean

- Does **not** mean delete ontology / GDR / Radar.
- Does **not** mean wait for 3 production friends (Phase 0) before coding — OSS ships synthetic methodology warehouse first; Phase 0 becomes an optional validation checklist in Concepts.
- Does **not** mean real-time streaming or prompt storage.
- Does **not** mean replacing Streamlit before M3 metrics are legible (implementation_plan P4 frontend pivot stays later).

---

## 8. Suggested sequencing for the next coding sessions

| Session | Ship |
| --- | --- |
| **A** | M0 docs + fix empty classifiers (`habit_collapse`, `connector_fragility`) + `experiment_id` stub on emit |
| **B** | M1 entity tables in generator + Workspace adapters |
| **C** | M2 five metrics + Activation/Economics page rebuild |
| **D** | M3 account health Radar mode + churn reason codes |
| **E** | M5 OTEL→AgentRun/Span ingestion |

---

## 9. Success criteria (product)

A new viewer can, after Generate workspace:

1. See **accounts** with days-to-first-verified-outcome and tourist risk.
2. See **delegation ratio** and **autonomy ratio** trend lines (not only boolean habit).
3. See **$/successful outcome** and a teaching **CM-NRR** by cohort.
4. Open a Decision Card whose exception maps to a **methodology churn reason** or core metric breach.
5. Still export/inspect a valid **GrowthDecisionRecord** (ontology IP intact).

If (1)–(4) work on synthetic data, churnOS becomes a faithful simulator of the methodology. If a real Langfuse+Stripe export later satisfies M5, it becomes the retention join product the methodology describes.
