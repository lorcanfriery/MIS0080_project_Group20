import os
import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st
from pandas_datareader import data as pdr

st_autorefresh(interval=60 * 60 * 1000, key="refresh")


os.environ["FRED_API_KEY"] = "5f7d4538d34756d81a77ee5b4b4bf2dd"


FRED_SERIES = {
    "CPI (All Items, Urban Consumers, SA)": "CPIAUCSL",
    "Core CPI (less food & energy, SA)": "CPILFESL",
    "PCE Price Index (SA)": "PCEPI",
    "Core PCE Price Index (SA)": "PCEPILFE",
    "5-Year Breakeven Inflation Expectation": "T5YIFR",
}


def fetch_fred_series(series_id: str, start: dt.date, end: dt.date) -> pd.Series:
    """
    Get time series from FRED via pandas-datareader.
    Returns a pandas Series with a DatetimeIndex.
    """
    df = pdr.DataReader(
        series_id,
        "fred",
        start,
        end,
        api_key=os.environ["FRED_API_KEY"],
    )
    if df.empty:
        return pd.Series(dtype="float64")
    s = df.iloc[:, 0]
    s.name = series_id
    return s


def compute_inflation_rates(level_series: pd.Series) -> pd.DataFrame:
    """
    Given a price index series (e.g., CPIAUCSL), compute:
      - YoY inflation rate (%)
      - MoM change (%)
    Assumes monthly frequency; resamples to monthly just in case.
    """
    if level_series.empty:
        return pd.DataFrame()

    m = level_series.resample("M").last()
    df = pd.DataFrame({"IndexLevel": m})

    df["MoM_%"] = df["IndexLevel"].pct_change() * 100
    df["YoY_%"] = df["IndexLevel"].pct_change(12) * 100

    return df



def render_inf_page():
    st.set_page_config(
        page_title="USD Inflation Dashboard (FRED)",
        layout="wide",
    )
    
    st.title("📈 USD Inflation Dashboard (FRED)")
    
    st.markdown(
        """
    This dashboard pulls **USD inflation-related data** directly from **FRED** using
    `pandas-datareader`.
    
    **Main default series:**  
    - `CPIAUCSL` – Consumer Price Index for All Urban Consumers (All Items, Seasonally Adjusted)
    
    You can switch to Core CPI, PCE, Core PCE, or 5-year breakeven inflation via the sidebar.
    """
    )
    
    st.sidebar.header("Data settings")
    
    series_label = st.sidebar.selectbox(
        "FRED series",
        options=list(FRED_SERIES.keys()),
        index=0,
    )
    
    series_id = FRED_SERIES[series_label]
    
    min_start_date = dt.date(1950, 1, 1)
    default_start = dt.date.today().replace(year=dt.date.today().year - 20)
    
    start_date = st.sidebar.date_input(
        "Start date",
        value=default_start,
        min_value=min_start_date,
    )
    
    end_date = st.sidebar.date_input(
        "End date",
        value=dt.date.today(),
    )
    
    show_table = st.sidebar.checkbox("Show data table", value=False)
    
    rolling_window = st.sidebar.slider(
        "Rolling average window (months)",
        min_value=1,
        max_value=24,
        value=6,
    )
    
    if start_date >= end_date:
        st.error("Start date must be before end date.")
        st.stop()
    
    with st.spinner(f"Fetching {series_id} from FRED..."):
        level_series = fetch_fred_series(series_id, start_date, end_date)
    
    if level_series.empty:
        st.error(
            f"No data returned for FRED series `{series_id}`. "
            "Check your API key and date range."
        )
        st.stop()
    
    df = compute_inflation_rates(level_series)
    
    if df.empty:
        st.error("Unable to compute inflation rates (empty dataset after processing).")
        st.stop()
    
    latest_row = df.dropna().iloc[-1]
    latest_date = latest_row.name.date()
    latest_yoy = latest_row["YoY_%"]
    latest_mom = latest_row["MoM_%"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=f"{series_label} (latest level)",
            value=f"{latest_row['IndexLevel']:.2f}",
        )
    
    with col2:
        st.metric(
            label=f"YoY % (as of {latest_date})",
            value=f"{latest_yoy:.2f}%",
        )
    
    with col3:
        st.metric(
            label=f"MoM % (as of {latest_date})",
            value=f"{latest_mom:.2f}%",
        )
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 YoY Inflation", "📈 Index Level", "📉 MoM Change"])
    
    df_reset = df.reset_index().rename(columns={"index": "DATE"})
    
    with tab1:
        fig_yoy = px.line(
            df_reset,
            x="DATE",
            y="YoY_%",
            title=f"Year-over-Year Inflation Rate (%) – {series_label}",
            labels={"DATE": "Date", "YoY_%": "YoY Inflation (%)"},
        )
        df_reset["YoY_rolling"] = df_reset["YoY_%"].rolling(window=rolling_window).mean()
    
    fig_yoy.add_scatter(
        x=df_reset["DATE"],
        y=df_reset["YoY_rolling"],
        mode="lines",
        name=f"YoY {rolling_window}-month avg",
    )
    st.plotly_chart(fig_yoy, use_container_width=True)
    
    with tab2:
        fig_level = px.line(
            df_reset,
            x="DATE",
            y="IndexLevel",
            title=f"Index Level – {series_label}",
            labels={"DATE": "Date", "IndexLevel": "Index Level"},
        )
        df_reset["Index_rolling"] = df_reset["IndexLevel"].rolling(window=rolling_window).mean()
    
    fig_level.add_scatter(
        x=df_reset["DATE"],
        y=df_reset["Index_rolling"],
        mode="lines",
        name=f"Index {rolling_window}-month avg",
    )
    st.plotly_chart(fig_level, use_container_width=True)
    
    with tab3:
        fig_mom = px.line(
            df_reset,
            x="DATE",
            y="MoM_%",
            title=f"Month-over-Month Change (%) – {series_label}",
            labels={"DATE": "Date", "MoM_%": "MoM Change (%)"},
        )
        df_reset["MoM_rolling"] = df_reset["MoM_%"].rolling(window=rolling_window).mean()
    
    fig_mom.add_scatter(
        x=df_reset["DATE"],
        y=df_reset["MoM_rolling"],
        mode="lines",
        name=f"MoM {rolling_window}-month avg",
    )
    st.plotly_chart(fig_mom, use_container_width=True)
    
    if show_table:
        st.dataframe(df.tail(200))
    
        st.subheader("Underlying data")
        st.dataframe(df.tail(200)) 
