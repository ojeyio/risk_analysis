import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import tempfile

st.set_page_config(layout="wide")
st.title("Portfolio Risk and Stress Testing")

# === Sidebar Input ===
st.sidebar.header("Input Parameters")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2006-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-01-01"))
tau = st.sidebar.number_input("Investment Horizon (days)", value=365 * 3)
delta = st.sidebar.number_input("Rolling Window (days)", value=22)
alpha = st.sidebar.slider("Confidence Level", 0.90, 0.99, 0.95)
fund_ids = st.sidebar.text_input("Fund IDs", "B00241,B01157,B07223,B10363,B12997,B14867").split(",")
weights = np.array(list(map(float, st.sidebar.text_input("Weights", "0.15,0.15,0.2,0.1,0.25,0.15").split(","))))

# === Load Data (Fixed Path) ===
def load_fund_data(filename, group):
    df = pd.read_csv(filename, parse_dates=["as_of"])
    df = df.melt(id_vars="as_of", var_name="fund_id", value_name="nav")
    df["fund_group"] = group
    return df

def load_holdings(filename, group):
    df = pd.read_csv(filename)
    df.rename(columns={"ask_id": "fund_id"}, inplace=True)
    df["fund_group"] = group
    return df

large = load_fund_data("large_cap.csv", "large_cap")
mid = load_fund_data("mid_cap.csv", "mid_cap")
agg = load_fund_data("us_agg.csv", "us_agg")
df_nav = pd.concat([large, mid, agg])
df_nav = df_nav[(df_nav["as_of"] >= pd.to_datetime(start_date)) & (df_nav["as_of"] <= pd.to_datetime(end_date))]

df_sample = df_nav[df_nav["fund_id"].isin(fund_ids)]
df_pivot = df_sample.pivot(index="as_of", columns="fund_id", values="nav").dropna()

returns = []
for col in df_pivot.columns:
    nav = df_pivot[col]
    r = [(nav.iloc[j + tau] - nav.iloc[j]) / nav.iloc[j] for j in range(0, len(nav) - tau, delta)]
    returns.append(r)
df_returns = pd.DataFrame(returns).T.dropna()
portfolio_returns = df_returns.dot(weights)

VaR_95 = np.percentile(portfolio_returns, (1 - alpha) * 100)
CVaR_95 = portfolio_returns[portfolio_returns <= VaR_95].mean()

h1 = load_holdings("large_cap_holding_data.csv", "large_cap")
h2 = load_holdings("mid_cap_holding_data.csv", "mid_cap")
h3 = load_holdings("us_agg_holding_data.csv", "us_agg")
holdings = pd.concat([h1, h2, h3])
sampled_holdings = holdings[holdings["fund_id"].isin(df_pivot.columns)].copy()
sector_columns = [col for col in sampled_holdings.columns if "equity_econ_sector" in col and "_pct_long_rs" in col]
sector_exposure = sampled_holdings[sector_columns].mean().sort_values(ascending=False)

def apply_stress(sector_col, shock):
    exposure_map = sampled_holdings.groupby("fund_id")[sector_col].mean()
    stressed = {}
    for fid in df_returns.columns:
        r = df_returns[fid]
        e = exposure_map.get(fid, 0.0) / 100
        stressed[fid] = r + shock * e
    stressed_returns = pd.DataFrame(stressed).dot(weights)
    var = np.percentile(stressed_returns, (1 - alpha) * 100)
    cvar = stressed_returns[stressed_returns <= var].mean()
    return var, cvar

sector_random = sector_exposure.index[0]
sector_tech = [s for s in sector_exposure.index if "technology" in s][0]
var_rand, cvar_rand = apply_stress(sector_random, -0.2)
var_tech, cvar_tech = apply_stress(sector_tech, -0.2)

st.subheader("Results")
st.write(f"Historical VaR (95%): **{VaR_95:.4f}**")
st.write(f"Historical CVaR (95%): **{CVaR_95:.4f}**")
st.write(f"Stress VaR ({sector_random}): **{var_rand:.4f}**")
st.write(f"Stress CVaR ({sector_random}): **{cvar_rand:.4f}**")
st.write(f"Stress VaR (Technology): **{var_tech:.4f}**")
st.write(f"Stress CVaR (Technology): **{cvar_tech:.4f}**")

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
    with PdfPages(tmp.name) as pdf:
        plt.figure(figsize=(10, 6))
        plt.hist(portfolio_returns, bins=50, density=True, alpha=0.6, color="skyblue", edgecolor="black")
        plt.axvline(VaR_95, color="red", linestyle="--", label=f"VaR = {VaR_95:.2%}")
        plt.axvline(CVaR_95, color="black", linestyle=":", label=f"CVaR = {CVaR_95:.2%}")
        plt.title("Historical Portfolio Return Distribution")
        plt.xlabel("Return")
        plt.ylabel("Density")
        plt.legend()
        pdf.savefig()
        plt.close()

        fig, ax = plt.subplots(figsize=(8, 2))
        ax.axis("off")
        rows = [["Historical VaR (95%)", f"{VaR_95:.4f}"],
                ["Historical CVaR (95%)", f"{CVaR_95:.4f}"],
                [f"Stress VaR ({sector_random})", f"{var_rand:.4f}"],
                [f"Stress CVaR ({sector_random})", f"{cvar_rand:.4f}"],
                ["Stress VaR (Technology)", f"{var_tech:.4f}"],
                ["Stress CVaR (Technology)", f"{cvar_tech:.4f}"]]
        table = ax.table(cellText=rows, colLabels=["Metric", "Value"], loc="center")
        table.scale(1.2, 1.5)
        pdf.savefig()
        plt.close()

    st.download_button("Download PDF Report", tmp.name, file_name="VaR_CVaR_Report.pdf")