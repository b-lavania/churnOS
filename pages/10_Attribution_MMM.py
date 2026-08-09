import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from core.workspace import get_workspace_from_session
from data.generator import generate_all_data
from analytics.attribution import build_and_sample_mmm, extract_roas_posteriors, posterior_predictive_check

st.set_page_config(page_title="Attribution MMM", layout="wide")

# Load CSS
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.markdown('<div class="terminal-header">MARKETING // BAYESIAN MMM</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text">Marketing Mix Modeling</h1>', unsafe_allow_html=True)

with st.expander("Concept Playbook: How to use this page"):
    st.markdown('''
    **Overview:** This page provides causal insights into your metrics.
    **How to use:** Adjust the inputs in the sidebar or main area to simulate different business scenarios. 
    Pay attention to the outputs with tooltips for detailed definitions. All metrics are connected to the central causal model.
    ''')


ws = get_workspace_from_session(st.session_state)
if ws is not None:
    df = ws.marketing
else:
    df = generate_all_data()["marketing"]

st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Model Configuration")
    adstock_decay = st.slider("Adstock decay", 0.0, 0.95, 0.5, 0.05)
    use_seasonality = st.checkbox("Weekly seasonality (2 harmonics)", value=True)
    st.write("Run the PyMC NUTS sampler to estimate causal ROAS.")
    run_model = st.button("Run Bayesian Sampler", type="primary")
    
    st.markdown("""
    > [!TIP]
    > **Why Bayesian?** Traditional last-click attribution under-reports top-of-funnel channels and over-reports bottom-of-funnel channels. A Bayesian MMM looks at aggregate spend vs sales to infer true causality and gives you a probability distribution, not just a single guess.
    """)

# Cache the heavy PyMC execution
@st.cache_data(show_spinner=False)
def get_model_trace(_df, _adstock, _seasonality):
    trace, model = build_and_sample_mmm(
        _df, adstock_decay=_adstock, use_seasonality=_seasonality,
    )
    roas_posteriors = extract_roas_posteriors(trace, _df, adstock_decay=_adstock)
    ppc = posterior_predictive_check(trace, _df, adstock_decay=_adstock, use_seasonality=_seasonality)
    return roas_posteriors, ppc

if run_model or "roas_posteriors" in st.session_state:
    with st.spinner("Sampling from posterior... (This may take a minute)"):
        roas_posteriors, ppc = get_model_trace(df, adstock_decay, use_seasonality)
        st.session_state["roas_posteriors"] = roas_posteriors
        st.session_state["mmm_ppc"] = ppc
        
    with col2:
        st.subheader("Posterior ROAS Distributions (95% HDI)")
        
        fig = go.Figure()
        channels = ["Meta", "Google", "TikTok", "Email"]
        colors = ["#1877F2", "#EA4335", "#00f2ff", "#14b8a6"]
        
        for i, c in enumerate(channels):
            fig.add_trace(go.Violin(
                x=roas_posteriors[c],
                name=c,
                line_color=colors[i],
                fillcolor=colors[i],
                opacity=0.6,
                meanline_visible=True
            ))
            
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)", 
            font=dict(color="#94a3b8"),
            xaxis_title="Estimated True ROAS (x)",
            yaxis_title="Channel",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        ppc = st.session_state.get("mmm_ppc", ppc)
        if ppc:
            st.subheader("Posterior predictive check (holdout 4 weeks)")
            fig_ppc = go.Figure()
            fig_ppc.add_trace(go.Scatter(y=ppc["observed"], name="Observed", mode="lines+markers"))
            fig_ppc.add_trace(go.Scatter(y=ppc["predicted"], name="Posterior predictive", mode="lines+markers"))
            fig_ppc.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
            )
            st.plotly_chart(fig_ppc, use_container_width=True)
            st.caption(f"Train RMSE: {ppc.get('train_rmse', 0):,.0f}")
        
    st.markdown("---")
    st.subheader("Budget Optimization Simulator")
    
    st.write("Adjust weekly budget below to see how diminishing returns impact expected revenue.")
    
    means = {c: np.mean(roas_posteriors[c]) for c in channels}
    
    opt_cols = st.columns(4)
    budget_allocs = {}
    for i, c in enumerate(channels):
        current_weekly = df[f"Spend_{c}"].sum() / 52
        budget_allocs[c] = opt_cols[i].slider(f"{c} Weekly ($)", 0, int(current_weekly*3), int(current_weekly), step=500)
        
    projected_rev = sum(budget_allocs[c] * means[c] for c in channels)
    st.metric("Expected Weekly Revenue from Ads", f"${projected_rev:,.2f}", help="The total amount of income generated by the sale of goods or services related to the company's primary operations.")
else:
    with col2:
        st.info("Click 'Run Bayesian Sampler' to initialize the PyMC engine.")
        
        st.subheader("Historical Daily Spend")
        fig = px.line(df, x="Date", y=["Spend_Meta", "Spend_Google", "Spend_TikTok", "Spend_Email"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"))
        st.plotly_chart(fig, use_container_width=True)
