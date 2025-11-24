# Second iteration of Project ~ Imports 
from fredapi import Fred
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
from streamlit_plotly_events import plotly_events

fred = Fred(api_key="e5f01fd50421590fffaebf8fec19052a")

# Currency data ~ If data in terms of 1 USD = True, if not = False
currencies = {
    "USDEUR": {"fred_id": "DEXUSEU", "is_usd_based": False},
    "USDGBP": {"fred_id": "DEXUSUK", "is_usd_based": False},
    "USDJPY": {"fred_id": "DEXJPUS", "is_usd_based": True},
    "USDAUD": {"fred_id": "DEXUSAL", "is_usd_based": False},
    "USDCAD": {"fred_id": "DEXCAUS", "is_usd_based": True},
    "USDCHF": {"fred_id": "DEXSZUS", "is_usd_based": True},
}

# Making a dynamic date range
def get_date_range(period: str):
    end = datetime.today()
    if period == "1D":
        start = end - timedelta(days=1)
    elif period == "1M":
        start = end - timedelta(days=30)
    elif period == "1Y":
        start = end - timedelta(days=365)
    elif period == "5Y":
        start = end - timedelta(days=365*5)
    elif period == "MAX":
        start = datetime(2015, 1, 1)
    else:
        raise ValueError("Invalid period")
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# Converting FX rates to USD terms
def convert_to_usd_strength(series: pd.Series, is_usd_based: bool) -> pd.Series:
    pct = series.pct_change()
    if is_usd_based:
        return pct
    else:
        return -pct
    
# Streamlit layout
st.title("USD vs World — FX Performance")

period = st.selectbox(
    "Select date range",
    ["1D", "1M", "1Y", "5Y", "MAX"],
    index=2  # default to "1Y")
)
START, END = get_date_range(period)
st.write(f"Showing data from **{START}** to **{END}**")

# Get FX levels from FRED
fx_levels = pd.DataFrame()

for pair, meta in currencies.items():
    s = fred.get_series(
        meta["fred_id"],
        observation_start=START,
        observation_end=END)
    fx_levels[pair] = s

# Drop rows where all FX levels are Na
fx_levels = fx_levels.dropna(how="all")
if fx_levels.empty:
    st.warning("No FX data available for this date range. Try a longer range.")
    st.stop()

#Calculate daily returns in USD terms
usd_ret = pd.DataFrame(index=fx_levels.index)
for pair, meta in currencies.items():
    usd_ret[pair] = convert_to_usd_strength(
        fx_levels[pair],
        meta["is_usd_based"]
    )
usd_ret = usd_ret.fillna(0)

# Build a USD-strength index that starts at 1.0
usd_index = (1 + usd_ret).cumprod()

# Overall % change from START to END
usd_change_pct = (usd_index.iloc[-1] - 1) * 100

#Visualization using Plotly for interactivity
bar_df = pd.DataFrame({
    "Currency": usd_change_pct.index,
    "USD_Change_Pct": usd_change_pct.values
})

fig_bar = px.bar(
    bar_df,
    x="USD_Change_Pct",
    y="Currency",
    orientation="h",
    labels={
        "USD_Change_Pct": "Change in USD Strength (%)",
        "Currency": "Currency"
    },
    title=f"USD vs World – FX Performance ({START} to {END})"
)

fig_bar.update_traces(
    marker_color=bar_df["USD_Change_Pct"].apply(lambda x: "green" if x >= 0 else "red")
)

fig_bar.update_layout(
    xaxis_title="Change (%)",
    yaxis_title="Currency",
    height=500,
    dragmode=False,
    modebar_remove=["editInChart"]
)


st.plotly_chart(fig_bar, use_container_width=True)

# Additional individual currency history plot
st.subheader("Individual currency history")

#User choices of currency and raw vs % change
currency_choice = st.selectbox(
    "Select currency to view FX history",
    fx_levels.columns.tolist(),
)

normalize = st.checkbox(
    "Show % change from start instead of raw FX rate",
    value=True,
)

# Line chart of selected currency
series = fx_levels[currency_choice].dropna()
if series.empty:
    st.warning("No data available for this currency in the selected date range.")
else:
    if normalize:
        
        base = series.iloc[0]
        series_to_plot = (series / base - 1) * 100
        ylabel = "% change vs start"
        title_extra = " (% change from start)"
    else:
        series_to_plot = series
        ylabel = "FX rate (as per FRED series)"
        title_extra = ""

    # Plotting the additional line chart with matplotlib
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(series_to_plot.index, series_to_plot.values)
    ax2.set_title(f"{currency_choice} – FX history{title_extra}")
    ax2.set_xlabel("Date")
    ax2.set_ylabel(ylabel)
    fig2.tight_layout()

st.pyplot(fig2, use_container_width=True)


