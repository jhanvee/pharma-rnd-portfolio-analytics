from pathlib import Path
import sys
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analysis import deterministic_summary, run_monte_carlo

st.set_page_config(page_title="R&D Portfolio Analytics", page_icon="🧪", layout="wide")
st.title("Pharmaceutical R&D Portfolio Analytics")
st.caption("Independent learning project • hypothetical programmes and assumptions only")

df = pd.read_csv(ROOT / "data" / "pipeline.csv")
with st.sidebar:
    st.header("Simulation settings")
    n_sims = st.select_slider("Monte Carlo simulations", options=[1000, 2500, 5000, 10000, 20000], value=10000)
    seed = st.number_input("Random seed", min_value=1, max_value=99999, value=42, step=1)
    st.caption("Changing the seed changes simulated outcomes. This is a simplified educational model.")

st.subheader("Pipeline assumptions")
edited = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="fixed")
st.caption("All inputs are fictional. Units are USD millions unless otherwise stated.")

summary = deterministic_summary(edited)
draws, portfolio = run_monte_carlo(edited, int(n_sims), int(seed))
mc = draws.groupby("programme")["npv_m"].agg(
    mean_npv_m="mean", median_npv_m="median",
    p10_npv_m=lambda x: x.quantile(0.10),
    p90_npv_m=lambda x: x.quantile(0.90),
    probability_positive_npv=lambda x: (x > 0).mean()
).reset_index()

c1, c2, c3 = st.columns(3)
c1.metric("Programmes", f"{len(edited)}")
c2.metric("Mean simulated portfolio NPV", f"${portfolio.portfolio_npv_m.mean():,.0f}m")
c3.metric("Chance portfolio NPV > 0", f"{(portfolio.portfolio_npv_m > 0).mean():.1%}")

left, right = st.columns(2)
with left:
    st.markdown("### Risk-adjusted NPV by programme")
    fig = px.bar(summary.sort_values("risk_adjusted_npv_m"), x="risk_adjusted_npv_m", y="programme",
                 orientation="h", hover_data=["therapy_area", "current_stage", "base_success_probability"])
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown("### Simulated NPV range")
    fig2 = px.box(draws, x="programme", y="npv_m", points=False)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Deterministic valuation")
st.dataframe(summary, use_container_width=True, hide_index=True)
st.markdown("### Monte Carlo outcomes")
st.dataframe(mc, use_container_width=True, hide_index=True)

st.markdown("### Portfolio NPV distribution")
fig3 = px.histogram(portfolio, x="portfolio_npv_m", nbins=60, marginal="box")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("### Interpretation checklist")
st.write("""
- Compare risk-adjusted value with remaining development spend, not just peak sales.
- Examine downside percentiles as well as the mean; a positive average can hide material downside.
- Test whether rankings change when launch timing, costs, discount rates or success probabilities change.
- Do not interpret these illustrative results as real drug valuations or clinical probabilities.
""")

st.download_button("Download programme assumptions (CSV)", edited.to_csv(index=False), "pipeline_assumptions.csv", "text/csv")
st.download_button("Download valuation summary (CSV)", summary.to_csv(index=False), "programme_valuation_summary.csv", "text/csv")
st.download_button("Download simulation draws (CSV)", draws.to_csv(index=False), "monte_carlo_draws.csv", "text/csv")
