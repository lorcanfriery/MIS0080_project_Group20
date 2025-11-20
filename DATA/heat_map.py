import streamlit as st

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load your dataset
df = pd.read_csv(r'C:\Users\lorca\Downloads\Programming project\DATA\macro_data.csv')

st.title("Global Economics – Correlation Heatmap")

# Select GDP or inflation to build heatmap
metric = st.radio(
    "Select a metric:",
    ["gdp_growth", "inflation"]
)
all_countries = sorted(df["country"].unique())
selected_countries = st.multiselect(
    "Select countries (at least 2):",
    all_countries,
    default=all_countries[:5])

if len(selected_countries) < 2:
    st.info("Please select at least two countries to see the correlation heatmap.")
else:
    # Filter data to selected countries only
    df_sel = df[df["country"].isin(selected_countries)]



# Pivot data so each country becomes a column
pivot = df.pivot(index="year", columns="country", values=metric)

pivot = pivot.dropna(how="any")
# Compute correlation between countries
corr = pivot.corr()

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, cmap="coolwarm", annot=False, ax=ax)
ax.set_title(f"Correlation Heatmap for {metric.replace('_', ' ').title()}")

st.pyplot(fig)
