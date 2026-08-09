import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt


def geometric_adstock(x: np.ndarray, decay: float) -> np.ndarray:
    """Geometric adstock transform."""
    out = np.zeros_like(x, dtype=float)
    carry = 0.0
    for i, v in enumerate(x):
        carry = v + decay * carry
        out[i] = carry
    return out


def fourier_seasonality(t: np.ndarray, period: float = 52.0, n_harmonics: int = 2) -> np.ndarray:
    """Weekly seasonality via Fourier terms."""
    cols = []
    for k in range(1, n_harmonics + 1):
        cols.append(np.sin(2 * np.pi * k * t / period))
        cols.append(np.cos(2 * np.pi * k * t / period))
    return np.column_stack(cols) if cols else np.zeros((len(t), 0))


def build_and_sample_mmm(
    df: pd.DataFrame,
    tune=300,
    draws=500,
    *,
    adstock_decay: float = 0.5,
    use_seasonality: bool = True,
):
    """Builds and samples a Bayesian MMM using PyMC with adstock + seasonality."""
    channels = ["Meta", "Google", "TikTok", "Email"]

    X = {}
    for c in channels:
        col = f"Spend_{c}"
        raw = df[col].values.astype(float)
        X[c] = geometric_adstock(raw, adstock_decay)

    y = df["Sales"].values
    t_idx = np.arange(len(df), dtype=float)
    season = fourier_seasonality(t_idx) if use_seasonality else np.zeros((len(df), 0))

    with pm.Model() as mmm:
        baseline = pm.HalfNormal("Baseline", sigma=y.mean())
        sigma = pm.HalfNormal("sigma", sigma=y.std())
        mu = baseline

        if use_seasonality and season.shape[1] > 0:
            season_coef = pm.Normal("season_coef", mu=0, sigma=y.std() * 0.1, shape=season.shape[1])
            mu = mu + pt.dot(season, season_coef)

        for c in channels:
            alpha = pm.HalfNormal(f"alpha_{c}", sigma=y.mean())
            beta = pm.Exponential(f"beta_{c}", lam=1 / (X[c].mean() + 1))
            channel_effect = alpha * (1 - pm.math.exp(-beta * X[c]))
            mu = mu + channel_effect

        sales_obs = pm.Normal("sales_obs", mu=mu, sigma=sigma, observed=y)
        trace = pm.sample(draws=draws, tune=tune, chains=2, cores=1, progressbar=False, random_seed=42)

    return trace, mmm


def posterior_predictive_check(
    trace,
    df: pd.DataFrame,
    *,
    holdout_weeks: int = 4,
    adstock_decay: float = 0.5,
    use_seasonality: bool = True,
) -> dict:
    """Observed vs posterior predictive mean on holdout."""
    channels = ["Meta", "Google", "TikTok", "Email"]
    y = df["Sales"].values
    n = len(y)
    holdout = min(holdout_weeks, n // 4)
    train_end = n - holdout

    post = trace.posterior
    baseline = post["Baseline"].values.mean()
    pred_train = np.full(train_end, baseline)
    for c in channels:
        spend = geometric_adstock(df[f"Spend_{c}"].values[:train_end], adstock_decay)
        alpha = post[f"alpha_{c}"].values.mean()
        beta = post[f"beta_{c}"].values.mean()
        pred_train += alpha * (1 - np.exp(-beta * spend))

    pred_holdout = np.full(holdout, baseline)
    for c in channels:
        spend = geometric_adstock(df[f"Spend_{c}"].values[train_end:], adstock_decay)
        alpha = post[f"alpha_{c}"].values.mean()
        beta = post[f"beta_{c}"].values.mean()
        pred_holdout += alpha * (1 - np.exp(-beta * spend))

    observed_holdout = y[train_end:]
    return {
        "observed": observed_holdout.tolist(),
        "predicted": pred_holdout.tolist(),
        "train_rmse": float(np.sqrt(np.mean((y[:train_end] - pred_train) ** 2))),
    }


def extract_roas_posteriors(trace, df: pd.DataFrame, adstock_decay: float = 0.5):
    """Extracts True ROAS posterior distributions from the trace."""
    channels = ["Meta", "Google", "TikTok", "Email"]
    roas_data = {}

    post = trace.posterior

    for c in channels:
        alpha = post[f"alpha_{c}"].values.flatten()
        beta = post[f"beta_{c}"].values.flatten()

        spend = geometric_adstock(df[f"Spend_{c}"].values, adstock_decay)
        total_spend = spend.sum()

        contribution = alpha[:, None] * (1 - np.exp(-beta[:, None] * spend[None, :]))
        total_contribution = contribution.sum(axis=1)

        roas = total_contribution / total_spend if total_spend > 0 else np.zeros_like(total_contribution)
        roas_data[c] = roas

    return roas_data
