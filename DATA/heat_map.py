import streamlit as st

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

all_countries = sorted(df["country"].unique())

default_list={c for c in all_countries if c in ["United States", "China", "India", "Germany", "Brazil"]}
if len(default_list) < 2:
    default_list = set(all_countries[:5])

selected_countries = st.multiselect(  
    "Select countries (at least 2):",
    all_countries,
    default=list(default_list)
)

if len(selected_countries) < 2:
    st.info("Please select at least two countries to display the heatmap.")
else:
    df_sel=df[df["country"].isin(selected_countries)].copy()

# Pivot data so each country becomes a column
pivot = df_sel.pivot(index="year", columns="country", values=metric)

pivot = pivot.dropna(axis=1, how="all")

if pivot.shape[1] < 2:
    st.warning("Not enough data to compute correlations for the selected countries.")
else:
# Compute correlation between countries
    corr = pivot.corr()

if corr.isna().all().all():
    st.warning("Correlation could not be computed (too many missing values). Try fewer countries.")

else:
# Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, cmap="coolwarm", annot=False, fmt=".2f", vmin=-1, vmax=1, ax=ax)
    ax.set_title(f"Correlation Heatmap for {metric.replace('_', ' ').title()}")

    st.pyplot(fig)
