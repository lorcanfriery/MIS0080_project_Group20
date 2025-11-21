print("hello world")
print("hello again")
print("new")




# First iteration of Project ~ Imports 
from fredapi import Fred
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np

fred = Fred(api_key="e5f01fd50421590fffaebf8fec19052a")

# Currency data ~ If data in terms of 1 USD = True, if not = False
currencies = {
    "EURUSD": {"fred_id": "DEXUSEU", "is_usd_based": False},
    "GBPUSD": {"fred_id": "DEXUSUK", "is_usd_based": False},
    "USDJPY": {"fred_id": "DEXJPUS", "is_usd_based": True},
    "AUDUSD": {"fred_id": "DEXUSAL", "is_usd_based": False},
    "USDCAD": {"fred_id": "DEXCAUS", "is_usd_based": True},
    "USDCHF": {"fred_id": "DEXSZUS", "is_usd_based": True},
}
START = "2015-01-01"
END = datetime.today().strftime("%Y-%m-%d")

# Converting FX rates to USD terms
def convert_to_usd_strength(series: pd.Series, is_usd_based: bool) -> pd.Series:
    pct = series.pct_change()
    if is_usd_based:
        return pct
    else:
        return -pct

# Get FX levels from FRED
fx_levels = pd.DataFrame()

for pair, meta in currencies.items():
    s = fred.get_series(
        meta["fred_id"],
        observation_start=START,
        observation_end=END
    )
    fx_levels[pair] = s

# Drop rows where all FX levels are Na
fx_levels = fx_levels.dropna(how="all")
print("Raw FX levels:")
print(fx_levels.head())

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
print("\nUSD strength change over period (%):")
print(usd_change_pct)

# Visualization (Horizontal Bar Chart)
pairs = usd_change_pct.index.tolist()
values = usd_change_pct.values
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.barh(pairs, values)

# Colours:  green if USD stronger (positive), red if weaker (negative)
for bar, val in zip(bars, values):
    bar.set_color("green" if val > 0 else "red")

ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Change in USD strength vs currency (%)")
ax.set_title(f"USD vs World — FX Performance ({START} to {END})")

# Adding % labels at the end of each bar
for bar, val in zip(bars, values):
    x = bar.get_width()
    y = bar.get_y() + bar.get_height() / 2
    offset = 0.3 if val >= 0 else -0.3
    ha = "left" if val >= 0 else "right"
    ax.text(x + offset, y, f"{val:.1f}%", va="center", ha=ha)


plt.tight_layout()
plt.show()
