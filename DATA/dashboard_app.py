import streamlit as st
import pandas as pd

df = pd.read_csv(r'C:\Users\lorca\Downloads\Programming project\DATA\macro_data.csv')
             
st.title('Global Economics Dashboard')
country = st.selectbox("Select a country:", sorted(df["country"].unique()))
metric = st.radio("Select a metric:", ["gdp_growth", "inflation"])
filtered = df[df["country"] == country]
st.line_chart(filtered.set_index("year")[metric])

years = st.slider("Select year range:", int(df["year"].min()), int(df["year"].max()), (2000, 2024))
filtered=filtered[(filtered["year"] >= years[0]) & (filtered["year"] <= years[1])]





