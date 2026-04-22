import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt

def build_and_sample_mmm(df: pd.DataFrame, tune=300, draws=500):
    """Builds and samples a Bayesian MMM using PyMC."""
    channels = ["Meta", "Google", "TikTok", "Email"]
    
    X = {}
    for c in channels:
        col = f"Spend_{c}"
        X[c] = df[col].values
        
    y = df["Sales"].values
    
    # We use a very simplified model for speed in the Streamlit app.
    # Diminishing returns: alpha * (1 - exp(-beta * spend))
    
    with pm.Model() as mmm:
        # Intercept / Baseline sales
        baseline = pm.HalfNormal("Baseline", sigma=y.mean())
        
        # Noise
        sigma = pm.HalfNormal("sigma", sigma=y.std())
        
        mu = baseline
        
        alpha_vars = {}
        beta_vars = {}
        
        for c in channels:
            alpha = pm.HalfNormal(f"alpha_{c}", sigma=y.mean())
            beta = pm.Exponential(f"beta_{c}", lam=1 / (X[c].mean() + 1))
            
            alpha_vars[c] = alpha
            beta_vars[c] = beta
            
            channel_effect = alpha * (1 - pm.math.exp(-beta * X[c]))
            mu = mu + channel_effect
            
        # Likelihood
        sales_obs = pm.Normal("sales_obs", mu=mu, sigma=sigma, observed=y)
        
        # Sample (cores=1, chains=2 for speed)
        trace = pm.sample(draws=draws, tune=tune, chains=2, cores=1, progressbar=False, random_seed=42)
        
    return trace, mmm

def extract_roas_posteriors(trace, df: pd.DataFrame):
    """Extracts True ROAS posterior distributions from the trace."""
    channels = ["Meta", "Google", "TikTok", "Email"]
    roas_data = {}
    
    post = trace.posterior
    
    for c in channels:
        alpha = post[f"alpha_{c}"].values.flatten()
        beta = post[f"beta_{c}"].values.flatten()
        
        spend = df[f"Spend_{c}"].values
        total_spend = spend.sum()
        
        contribution = alpha[:, None] * (1 - np.exp(-beta[:, None] * spend[None, :]))
        total_contribution = contribution.sum(axis=1)
        
        roas = total_contribution / total_spend if total_spend > 0 else np.zeros_like(total_contribution)
        roas_data[c] = roas
        
    return roas_data
