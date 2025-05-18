# risk_analysis
# Portfolio Risk and Stress Testing

This project estimates portfolio risk using Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR), with optional stress testing across equity sectors. It uses historical Net Asset Value (NAV) data and sector-level exposure from fund holdings.

## Features
- Historical VaR and CVaR estimation
- Sector-based stress testing (e.g., Technology shock)
- Generates a downloadable PDF report
- Accepts user-defined parameters (dates, weights, confidence level)
- Works in:
  - Command-line / Python IDE (`risk_analysis.py`)
  - Web app via Streamlit (`risk_dashboard.py`)

---

## File Structure

project_folder/
├── risk_analysis.py
├── risk_dashboard.py
├── large_cap.csv
├── mid_cap.csv
├── us_agg.csv
├── large_cap_holding_data.csv
├── mid_cap_holding_data.csv
├── us_agg_holding_data.csv
└── README.md