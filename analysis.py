from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pipeline.csv"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

def revenue_curve(peak_sales, launch_year, commercial_life, year):
    """Simple ramp: 20%, 50%, 75%, then 100% of peak sales; no terminal value."""
    t = year - launch_year
    if t < 0 or t >= commercial_life:
        return 0.0
    ramp = [0.20, 0.50, 0.75, 1.00]
    return float(peak_sales * ramp[min(t, len(ramp)-1)])

def programme_cash_flows(row, peak_sales=None, dev_cost=None, launch_delay=0.0):
    """Return annual un-risk-adjusted net cash flows from year 0 to horizon."""
    peak_sales = float(row.peak_sales_m if peak_sales is None else peak_sales)
    dev_cost = float(row.remaining_dev_cost_m if dev_cost is None else dev_cost)
    delay = max(0.0, float(launch_delay))
    launch_year = int(round(float(row.years_to_launch) + delay))
    horizon = max(launch_year + int(row.commercial_life_years), int(row.years_to_launch) + int(row.commercial_life_years)) + 1
    flows = np.zeros(horizon, dtype=float)
    # Spend remaining development cost in equal annual tranches before launch.
    spend_years = max(1, int(round(float(row.years_to_launch))))
    for y in range(spend_years):
        flows[y] -= dev_cost / spend_years
    for y in range(horizon):
        rev = revenue_curve(peak_sales, launch_year, int(row.commercial_life_years), y)
        flows[y] += rev * float(row.gross_margin) - float(row.annual_commercial_cost_m) * (1.0 if rev > 0 else 0.0)
    return flows

def npv(flows, rate):
    years = np.arange(len(flows))
    return float(np.sum(flows / ((1.0 + rate) ** years)))

def deterministic_summary(df):
    rows = []
    for _, r in df.iterrows():
        cf = programme_cash_flows(r)
        raw_npv = npv(cf, float(r.discount_rate))
        # Simplified rNPV: development spending is treated as certain; commercial cash flows
        # are weighted by the base probability of technical/commercial success.
        dev_only = np.minimum(cf, 0)
        commercial_only = np.maximum(cf, 0)
        rn = npv(dev_only, float(r.discount_rate)) + float(r.base_success_probability) * npv(commercial_only, float(r.discount_rate))
        rows.append({
            "programme": r.programme, "therapy_area": r.therapy_area, "current_stage": r.current_stage,
            "years_to_launch": int(r.years_to_launch), "base_success_probability": float(r.base_success_probability),
            "unrisked_npv_m": raw_npv, "risk_adjusted_npv_m": rn,
            "remaining_dev_cost_m": float(r.remaining_dev_cost_m), "peak_sales_m": float(r.peak_sales_m)
        })
    return pd.DataFrame(rows).sort_values("risk_adjusted_npv_m", ascending=False)

def run_monte_carlo(df, n_sims=10000, seed=42):
    rng = np.random.default_rng(seed)
    records = []
    portfolio = np.zeros(n_sims)
    for _, r in df.iterrows():
        p = np.clip(rng.normal(r.base_success_probability, r.success_probability_sd, n_sims), 0.01, 0.95)
        dev = np.maximum(1.0, rng.normal(r.remaining_dev_cost_m, r.remaining_dev_cost_m * r.dev_cost_cv, n_sims))
        sales = np.maximum(1.0, rng.lognormal(np.log(r.peak_sales_m) - 0.5 * np.log(1 + r.peak_sales_cv**2),
                                              np.sqrt(np.log(1 + r.peak_sales_cv**2)), n_sims))
        delay = np.maximum(0.0, rng.normal(0, r.launch_delay_sd_years, n_sims))
        value = np.zeros(n_sims)
        for i in range(n_sims):
            row = r.copy()
            cf = programme_cash_flows(row, peak_sales=sales[i], dev_cost=dev[i], launch_delay=delay[i])
            # Each draw has a Bernoulli success/failure outcome. If failure, commercial inflows are zero,
            # while development costs remain incurred in this simplified framework.
            success = rng.random() < p[i]
            if not success:
                cf = np.minimum(cf, 0)
            value[i] = npv(cf, float(r.discount_rate))
        portfolio += value
        records.append(pd.DataFrame({
            "programme": r.programme, "simulation": np.arange(n_sims),
            "npv_m": value, "sampled_success_probability": p, "sampled_dev_cost_m": dev,
            "sampled_peak_sales_m": sales, "sampled_launch_delay_years": delay
        }))
    draws = pd.concat(records, ignore_index=True)
    portfolio_df = pd.DataFrame({"simulation": np.arange(n_sims), "portfolio_npv_m": portfolio})
    return draws, portfolio_df

def main():
    df = pd.read_csv(DATA)
    summary = deterministic_summary(df)
    draws, portfolio = run_monte_carlo(df)
    summary.to_csv(OUT / "programme_summary.csv", index=False)
    draws.to_csv(OUT / "monte_carlo_sample.csv", index=False)
    mc = draws.groupby("programme")["npv_m"].agg(
        mean_npv_m="mean",
        median_npv_m="median",
        p10_npv_m=lambda x: x.quantile(0.10),
        p90_npv_m=lambda x: x.quantile(0.90),
        probability_positive_npv=lambda x: (x > 0).mean()
    ).reset_index()
    mc.to_csv(OUT / "monte_carlo_summary.csv", index=False)
    portfolio_summary = {
        "mean_portfolio_npv_m": portfolio.portfolio_npv_m.mean(),
        "median_portfolio_npv_m": portfolio.portfolio_npv_m.median(),
        "p10_portfolio_npv_m": portfolio.portfolio_npv_m.quantile(0.10),
        "p90_portfolio_npv_m": portfolio.portfolio_npv_m.quantile(0.90),
        "probability_positive_portfolio_npv": (portfolio.portfolio_npv_m > 0).mean()
    }
    pd.DataFrame([portfolio_summary]).to_csv(OUT / "portfolio_monte_carlo_summary.csv", index=False)
    print("Wrote outputs to", OUT)
    print(summary.to_string(index=False))
    print("\nMonte Carlo summary:\n", mc.to_string(index=False))
    print("\nPortfolio summary:\n", portfolio_summary)

if __name__ == "__main__":
    main()
