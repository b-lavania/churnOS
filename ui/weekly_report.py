"""Weekly Account Health Report — Retention Spec presentation on Radar."""

from __future__ import annotations

from typing import Any

import streamlit as st

from analytics.metrics import resolve_metric
from core.workspace import Workspace


def render_meta_chips(ws: Workspace, *, n_acc: int, n_cap: int) -> None:
    profile = ws.profile
    math_mode = profile.get("priors", {}).get("math_mode", "heuristic")
    chips = [
        profile.get("preset_id", "—"),
        profile.get("ontology_vertical", "—"),
        f"math:{math_mode}",
        f"seed {ws.seed}",
        f"{n_acc} acct GDRs",
        f"{n_cap} cap GDRs",
    ]
    html = " ".join(f'<span class="mag-meta-chip">{c}</span>' for c in chips)
    st.markdown(f'<div class="mag-meta-chips">{html}</div>', unsafe_allow_html=True)


def render_weekly_account_report(
    ws: Workspace,
    acc_records: list[dict[str, Any]],
) -> None:
    """Retention Spec §3.1 structure on synthetic account GDRs."""
    accounts = getattr(ws, "accounts", ws.workspaces)
    n_active = len(accounts)
    at_risk = [r for r in acc_records if r.get("risk_score", 0) >= 0.5]
    pct_at_risk = (len(at_risk) / n_active * 100) if n_active else 0.0
    cpso = resolve_metric("cost_per_successful_outcome", ws)

    st.markdown("#### Executive summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Active accounts", n_active)
    c2.metric("At-risk accounts", len(at_risk), delta=f"{pct_at_risk:.0f}% of base")
    c3.metric("CPSO trend", cpso["display"])

    st.markdown("#### At-risk account list")
    if not acc_records:
        st.info("No account GDRs — regenerate workspace or try another seed.")
        return

    table_rows = []
    for rec in acc_records[:12]:
        subj = rec.get("subject", {})
        dec = rec.get("decision", {})
        risk_display = rec.get("risk_score", "—")
        if rec.get("p_churn_30d") is not None:
            ci = rec.get("p_churn_ci95") or [0, 1]
            risk_display = f"{rec['p_churn_30d'] * 100:.0f}% ({ci[0] * 100:.0f}–{ci[1] * 100:.0f}%)"
        cost = rec.get("economics", {}).get("primary_metric_usd", 0)
        cost_ci = rec.get("cost_ci95_usd")
        cost_str = f"${cost:,.0f}"
        if cost_ci:
            cost_str = f"${cost:,.0f} ({cost_ci[0]:,.0f}–{cost_ci[1]:,.0f})"
        table_rows.append({
            "Account": subj.get("account_id", "—"),
            "Tier": subj.get("tier", "—"),
            "30d churn risk": risk_display,
            "Primary signal": rec.get("primary_signal", "—"),
            "Recommended": dec.get("recommended_action", "—"),
            "Cost live": cost_str,
        })
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.markdown("#### Agent health")
    h1, h2, h3 = st.columns(3)
    h1.metric("Verified success", resolve_metric("verified_outcome_success_rate", ws)["display"])
    h2.metric("Outcome drift WoW", resolve_metric("outcome_success_drift", ws)["display"])
    h3.metric("Autonomy ratio", resolve_metric("autonomy_ratio", ws)["display"])

    st.markdown("#### Margin watch")
    margin_recs = [
        r for r in acc_records
        if any(e.get("category") in ("price", "margin_leakage", "run_cost_blowout") for e in r.get("exceptions", []))
    ]
    if margin_recs:
        for r in margin_recs[:5]:
            st.caption(
                f"**{r['subject'].get('account_id')}** — "
                f"${r['economics'].get('primary_metric_usd', 0):,.0f} at risk · "
                f"{r.get('primary_signal', '')}"
            )
    else:
        st.caption("No margin-breach accounts flagged this seed.")
    from analytics.evidence import is_rigorous_mode
    from analytics.stochastic_economics import bootstrap_cm_nrr
    if ws and is_rigorous_mode(ws.profile):
        stoch = bootstrap_cm_nrr(ws)
        st.caption(
            f"Stochastic: {stoch['p_cm_nrr_below_1']:.0%} chance CM-NRR < 100% "
            f"(mean {stoch['cm_nrr_mean']:.0%})."
        )
