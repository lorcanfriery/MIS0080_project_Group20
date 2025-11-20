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

# Pivot data so each country becomes a column
pivot = df.pivot(index="year", columns="country", values=metric)

# Compute correlation between countries
corr = pivot.corr()

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, cmap="coolwarm", annot=False, ax=ax)
ax.set_title(f"Correlation Heatmap for {metric.replace('_', ' ').title()}")

st.pyplot(fig)
