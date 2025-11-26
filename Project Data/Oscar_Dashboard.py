import pandas as pd


infl = pd.read_csv("Project Data/oecd_inflation.csv")
gap  = pd.read_csv("Project Data/oecd_gdp_growth.csv")
rate = pd.read_csv("Project Data/oecd_policy_rate.csv")

selected_infl = infl[["Reference area","TIME_PERIOD", "OBS_VALUE"]]
selected_infl = selected_infl.rename(columns={"Reference area": "Country", "TIME_PERIOD": "Year", "OBS_VALUE": "Inflation Rate"})

selected_gap = gap[["Reference area","TIME_PERIOD", "OBS_VALUE"]]
selected_gap = selected_gap.rename(columns={"Reference area": "Country", "TIME_PERIOD": "Year", "OBS_VALUE": "GDP Growth"})

selected_rate = rate[["Reference area","TIME_PERIOD", "OBS_VALUE"]]
selected_rate = selected_rate.rename(columns={"Reference area": "Country", "TIME_PERIOD": "Year", "OBS_VALUE": "Policy Rate"})


merged_data = pd.merge(selected_infl, selected_rate, on=["Country", "Year"], how="inner")

# Convert "2000-Q1" → "2000-03"
quarter_to_month = {
    "Q1": "03",
    "Q2": "06",
    "Q3": "09",
    "Q4": "12"
}

def convert_quarter_to_month(value):
    year, quarter = value.split("-")
    month = quarter_to_month[quarter]
    return f"{year}-{month}"

selected_gap["Year"] = selected_gap["Year"].apply(convert_quarter_to_month)

final_data = pd.merge(merged_data, selected_gap, on=["Country", "Year"], how="inner")


final_data.to_csv("final_data.csv", index=False)

data = pd.read_csv("final_data.csv")

import streamlit as st
import plotly.express as px


# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_csv("final_data.csv")
    # make sure Year is a date if it's like YYYY-MM
    df["Year"] = pd.to_datetime(df["Year"])
    return df

df = load_data()

# ---------- SIDEBAR FILTERS ----------
st.sidebar.title("Filters")

# Country selector
countries = sorted(df["Country"].unique())
selected_country = st.sidebar.selectbox("Country", countries)

# Year range slider
min_year = int(df["Year"].dt.year.min())
max_year = int(df["Year"].dt.year.max())
year_range = st.sidebar.slider(
    "Year range",
    min_year,
    max_year,
    (min_year, max_year),
)

# Filter dataframe
mask = (
    (df["Country"] == selected_country)
    & (df["Year"].dt.year >= year_range[0])
    & (df["Year"].dt.year <= year_range[1])
)
filtered = df[mask]

# ---------- PAGE TITLE ----------
st.title("Macroeconomic Dashboard")
st.subheader(f"{selected_country}: {year_range[0]}–{year_range[1]}")

# ---------- KPIs / SUMMARY ----------
if not filtered.empty:
    latest = filtered.sort_values("Year").iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Inflation Rate (latest)", f"{latest['Inflation Rate']:.2f}%")
    col2.metric("GDP Growth (latest)", f"{latest['GDP Growth']:.2f}%")
    col3.metric("Policy Rate (latest)", f"{latest['Policy Rate']:.2f}%")
else:
    st.warning("No data for this selection.")

st.markdown("---")

# ---------- CHARTS ----------
if not filtered.empty:
    # GDP Growth
    fig_gdp = px.line(
        filtered,
        x="Year",
        y="GDP Growth",
        title="GDP Growth over time",
        markers=True,
    )
    st.plotly_chart(fig_gdp, use_container_width=True)

    # Inflation
    fig_infl = px.line(
        filtered,
        x="Year",
        y="Inflation Rate",
        title="Inflation Rate over time",
        markers=True,
    )
    st.plotly_chart(fig_infl, use_container_width=True)

    # Policy rate
    fig_rate = px.line(
        filtered,
        x="Year",
        y="Policy Rate",
        title="Policy Rate over time",
        markers=True,
    )
    st.plotly_chart(fig_rate, use_container_width=True)
else:
    st.info("Adjust filters to see charts.")
