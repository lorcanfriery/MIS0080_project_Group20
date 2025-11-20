import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load your dataset
df = pd.read_csv(r'C:\Users\lorca\Downloads\Programming project\DATA\macro_data.csv')

df = df[df["iso3c"].str.len() == 3].copy()

st.title("Global Economics – Correlation Heatmap")

# Select GDP or inflation to build heatmap
metric = st.radio(
    "Select a metric:",
    ["gdp_growth", "inflation"],
    format_func=lambda m: "GDP growth" if m == "gdp_growth" else "Inflation"
)
#toggle between single year and miltiple years
mode = st.radio(
    "Select correlation mode:",
    ["Single year (±1 year window)", "Year range"]
)

min_year = int(df["year"].min())
max_year = int(df["year"].max())

if mode == "Year range":
    year_range = st.slider(
        "Select year range:",
        min_year,
        max_year,
        (min_year, max_year)
    )
    year_filter = (df["year"] >= year_range[0]) & (df["year"] <= year_range[1])
    year_text = f"{year_range[0]}–{year_range[1]}"

else:
    selected_year = st.selectbox(
        "Select centre year:",
        sorted(df["year"].unique())
    )
    # use a small window around that year
    start_year = max(min_year, selected_year - 1)
    end_year = min(max_year, selected_year + 1)
    year_filter = (df["year"] >= start_year) & (df["year"] <= end_year)
    year_text = f"{selected_year} (window {start_year}–{end_year})"


# ---- Country presets ----
all_countries = sorted(df["country"].unique())

group = st.selectbox(
    "Quick country group:",
    ["Custom selection", "BRICS", "G7", "Euro Area Core"]
)

groups = {
    "BRICS": ["Brazil", "Russian Federation", "India", "China", "South Africa"],
    "G7": ["United States", "United Kingdom", "Germany", "France", "Italy", "Canada", "Japan"],
    "Euro Area Core": ["Germany", "France", "Belgium", "Netherlands", "Italy", "Spain"]
}

# Set default list depending on preset
if group == "Custom selection":
    default_list = ["United States", "China", "India", "Germany", "Brazil"]
else:
    default_list = [c for c in all_countries if c in groups[group]]

# ---- Country multi-select ----
selected_countries = st.multiselect(
    "Select countries (at least 2):",
    all_countries,
    default=default_list
)


if len(selected_countries) < 2:
    st.info("Please select at least two countries to display the heatmap.")
    st.stop()

df_sel=df[
    (df["country"].isin(selected_countries)) &
    year_filter
    ].copy()

if df_sel.empty:
    st.warning(f"No data available for the selected countries {year_text}. Please adjust your selection.")
    st.stop()

# Pivot data so each country becomes a column
pivot = df_sel.pivot(index="year", columns="country", values=metric)

pivot = pivot.dropna(axis=1, how="all")

if pivot.shape[1] < 2:
    st.warning("Not enough data to compute correlations for the selected countries.")
    st.stop()

# Compute correlation between countries
corr = pivot.corr()

if corr.isna().all().all():
    st.warning("Correlation could not be computed (too many missing values). Try fewer countries.")
    st.stop()

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, cmap="coolwarm", annot=True, fmt=".2f", vmin=-1, vmax=1, ax=ax)
ax.set_title(f"Correlation Heatmap for {metric.replace('_', ' ').title()}")

#Insight summary of strongest / weakest correlations 

corr_for_pairs = corr.copy()
corr_for_pairs.index.name = "Country A"
corr_for_pairs.columns.name = "Country B"

# Remove diagonal (self-correlations)
np.fill_diagonal(corr_for_pairs.values, np.nan)


mask = np.triu(np.ones_like(corr_for_pairs, dtype=bool))
corr_lower = corr_for_pairs.mask(mask)


corr_pairs = (
    corr_lower.stack()
    .reset_index(name="corr_value")
    .dropna(subset=["corr_value"])
)


if not corr_pairs.empty:
   
    best = corr_pairs.loc[corr_pairs["corr_value"].idxmax()]

  
    worst = corr_pairs.loc[corr_pairs["corr_value"].idxmin()]

    st.write(
        f"**Strongest positive correlation:** "
        f"{best['Country A']} & {best['Country B']} ({best['corr_value']:.2f})"
    )
    st.write(
        f"**Weakest (most negative) correlation:** "
        f"{worst['Country A']} & {worst['Country B']} ({worst['corr_value']:.2f})"
    )





st.pyplot(fig)
st.caption(
    f"Correlations are Pearson correlations of {metric.replace('_', ' ')} "
    f"between selected countries using data from {year_text}."
)

