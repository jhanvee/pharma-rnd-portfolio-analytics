# Pharmaceutical R&D Portfolio Valuation & Risk Analytics
**Independent learning project — hypothetical data only**

This project demonstrates a simple, transparent framework for comparing hypothetical drug-development programmes. It is not investment advice, a clinical forecast, or a validated pharmaceutical valuation model.

## Contents
- `data/pipeline.csv`: illustrative assumptions for five hypothetical programmes.
- `src/analysis.py`: NPV/rNPV calculations, scenario analysis, and Monte Carlo simulation.
- `src/app.py`: Streamlit dashboard.
- `outputs/programme_summary.csv`: deterministic programme valuation summary.
- `outputs/monte_carlo_summary.csv`: simulated portfolio and programme outcomes.
- `outputs/monte_carlo_sample.csv`: sample simulation draws for inspection.
- `outputs/investment_memo.md`: example decision memo based strictly on the illustrative model.
- `requirements.txt`: Python dependencies.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python src/analysis.py
streamlit run src/app.py
```

The dashboard expects to be run from this project folder.

## Method
For each programme, expected annual revenue is approximated using a simple peak-sales ramp, then multiplied by a gross margin and reduced by annual operating/commercial costs. Cash flows are discounted to the present. rNPV weights future cash flows by a simplified cumulative probability of technical success from the current stage; remaining development costs are also probability-weighted in this teaching model.

Monte Carlo simulations sample:
- clinical/commercial success probability around the stated base probability;
- remaining development cost around the base estimate;
- peak sales around the base estimate;
- launch delay around the stated uncertainty.

These are deliberately simplified assumptions. Real pharmaceutical valuation needs indication-specific epidemiology, pricing/access, patent/exclusivity, competition, development-stage transition probabilities, trial design, launch curves, tax, partnering economics, and expert review. The model should not be represented as a professional pharma valuation.

## Important
All programme names and assumptions are fictional. Do not present this as professional pharmaceutical experience. On your CV, call it an independent project only after you have personally run it, reviewed the results, and can explain the assumptions and limitations.
