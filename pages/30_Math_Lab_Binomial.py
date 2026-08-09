"""Math Lab — Beta–Binomial churn rate posteriors."""

from pathlib import Path

import streamlit as st

from analytics.evidence import churn_rate_evidence
from analytics.inference.binomial import beta_binomial_posterior
from core.workspace import get_workspace_from_session
from data.ground_truth import get as get_ground_truth
from ui.evidence_chrome import render_evidence_block, render_claim_badge
from ui.explain import page_help
from ui.magazine import load_magazine_css, masthead, section_kicker
from ui.workspace_banner import require_workspace

css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

load_magazine_css()
masthead("Learn", "Math Lab · Binomial", "Beta–Binomial posteriors on planted churn rates.")
page_help("math_lab")

ws = require_workspace(st.session_state, page_label="Math Lab")
seats = ws.seats
churned = int(seats["is_churned"].sum()) if not seats.empty and "is_churned" in seats.columns else 0
n = len(seats)
active = n - churned

section_kicker("Observed data")
c1, c2, c3 = st.columns(3)
c1.metric("Seats", n)
c2.metric("Churned", churned)
c3.metric("Point rate", f"{churned / n:.1%}" if n else "—")

post = beta_binomial_posterior(churned, n)
evidence = churn_rate_evidence(churned, n, claim_type="simulated")

section_kicker("Posterior")
st.write(f"Mean churn rate: **{post['mean']:.1%}**")
st.write(f"95% credible interval: **{post['ci95'][0]:.1%} – {post['ci95'][1]:.1%}**")
render_evidence_block(evidence)

gt = get_ground_truth(ws.seed)
if gt:
    section_kicker("Ground truth recovery")
    st.caption(f"Planted population churn rate: **{gt.population_churn_rate:.1%}**")
    err = abs(post["mean"] - gt.population_churn_rate)
    st.metric("Posterior mean error", f"{err:.2%}", help="Should shrink as n grows.")

section_kicker("Intuition")
st.markdown(
    """
Prior → likelihood → posterior. With uniform prior (α=β=1), the posterior mean is
**(successes + 1) / (trials + 2)** — shrinkage toward 50% when data is sparse.
On Radar, use the **interval**, not only the point rate, to decide if a cohort is worse or noise.
    """
)
