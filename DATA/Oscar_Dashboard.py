import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
def render_event_page():
    st.set_page_config(page_title="The Effect of Key Events on Macroeconomic Indicators", layout="wide")
    st.title("The Effect of Key Events on Macroeconomic Indicators")

    # Always use dark theme
    TEMPLATE = "plotly_dark"

    # ─────────────────────────────────────────
    # LOAD DATA
    # ─────────────────────────────────────────
    @st.cache_data
    def load_data():
        df = pd.read_csv("final_data.csv")
        # Year is in YYYY-MM format
        df["Date"] = pd.to_datetime(df["Year"], format="%Y-%m")
        return df


    df = load_data()

    required_cols = {
        "Country", "Year", "Date",
        "Inflation Rate", "Policy Rate", "GDP Growth"
    }
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Missing columns in final_data.csv: {missing}")
        st.stop()

    # ─────────────────────────────────────────
    # SIDEBAR CONTROLS
    # ─────────────────────────────────────────
    with st.sidebar:
        st.header("Controls")

        # Countries selector (multi-select)
        countries = sorted(df["Country"].unique())
        selected_countries = st.multiselect(
            "Select countries:",
            countries,
            default=[countries[0]] if countries else [],
        )

        if len(selected_countries) == 0:
            st.warning("Please select at least one country.")
            st.stop()

        # Metrics (max 2)
        metric_options = ["Inflation Rate", "Policy Rate", "GDP Growth"]
        selected_metrics = st.multiselect(
            "Select metrics (up to 2):",
            metric_options,
            default=["Inflation Rate"],
        )

        if len(selected_metrics) == 0:
            st.warning("Please select at least one metric.")
            st.stop()
        if len(selected_metrics) > 2:
            st.warning("Please select no more than two metrics.")
            st.stop()

        # Time slider based on selected countries' data
        country_df_all = df[df["Country"].isin(selected_countries)].sort_values("Date")
        min_date = country_df_all["Date"].min().to_pydatetime()
        max_date = country_df_all["Date"].max().to_pydatetime()

        selected_range = st.slider(
            "Select time range:",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM",
        )

    # ─────────────────────────────────────────
    # FILTER DATA
    # ─────────────────────────────────────────
    df_filtered = country_df_all[
        (country_df_all["Date"] >= selected_range[0]) &
        (country_df_all["Date"] <= selected_range[1])
    ].copy()

    if df_filtered.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    # ─────────────────────────────────────────
    # KEY EVENTS
    # ─────────────────────────────────────────
    key_events = [
        {
            "name": "9/11 Attacks",
            "start": "2001-09-01",
            "end": "2002-01-01",
            "color": "rgba(255, 215, 0, 0.25)",
            "explanation": "The 9/11 attacks in 2001 caused immediate global shock, disrupting U.S. financial markets, aviation, and investor confidence. GDP dipped, consumer spending fell, and markets saw sharp volatility, while risk premiums and uncertainty surged.",
        },
        {
            "name": "Financial Crisis",
            "start": "2008-09-01",
            "end": "2009-06-01",
            "color": "rgba(255, 0, 0, 0.25)",
            "explanation": "The 2008 financial crisis, triggered by a collapse in the U.S. housing market and systemic failures in global finance, led to severe economic contraction. GDP fell sharply, unemployment spiked, credit markets froze, and consumer and business confidence plummeted.",
        },
        {
            "name": "Brexit Referendum",
            "start": "2016-06-01",
            "end": "2017-01-01",
            "color": "rgba(0, 120, 255, 0.25)",
            "explanation": "The 2016 Brexit referendum created major political and economic uncertainty as the U.K. voted to leave the EU.The pound depreciated sharply, investment slowed, and financial markets experienced heightened volatility.",
        },
        {
            "name": "COVID-19 Shock",
            "start": "2020-03-01",
            "end": "2021-03-01",
            "color": "rgba(0, 180, 0, 0.25)",
            "explanation": "The COVID-19 pandemic caused an unprecedented global health and economic shock as countries imposed lockdowns and mobility restrictions.GDP contracted sharply, unemployment surged, supply chains broke down, and fiscal and monetary authorities deployed massive stimulus",
        },
    ]

    for ev in key_events:
        ev["start"] = pd.to_datetime(ev["start"])
        ev["end"] = pd.to_datetime(ev["end"])
        ev["mid"] = ev["start"] + (ev["end"] - ev["start"]) / 2

    # ─────────────────────────────────────────
    # MAIN LINE CHART
    # ─────────────────────────────────────────
    fig = go.Figure()

    # 1) Time-series lines for each (country, metric)
    for country in selected_countries:
        country_df = df_filtered[df_filtered["Country"] == country]
        for metric in selected_metrics:
            fig.add_trace(
                go.Scatter(
                    x=country_df["Date"],
                    y=country_df[metric],
                    mode="lines",
                    name=f"{country} – {metric}",
                    line_shape="spline",
                )
            )

    # 2) Correlation line if exactly 2 metrics (per country)
    if len(selected_metrics) == 2:
        m1, m2 = selected_metrics
        for country in selected_countries:
            country_df = df_filtered[df_filtered["Country"] == country]
            x_vals = country_df[m1].to_numpy()
            y_vals = country_df[m2].to_numpy()
            mask = (~np.isnan(x_vals)) & (~np.isnan(y_vals))

            if mask.sum() > 2:
                a, b = np.polyfit(x_vals[mask], y_vals[mask], 1)
                y_hat = a * x_vals[mask] + b

                fig.add_trace(
                    go.Scatter(
                        x=country_df["Date"][mask],
                        y=y_hat,
                        mode="lines",
                        name=f"Correlation line ({m1} → {m2}) – {country}",
                        line=dict(dash="dash", width=3),
                    )
                )

    # 3) Shaded key events with centered titles + hover explanations
    max_y = df_filtered[selected_metrics].max().max()

    for ev in key_events:
        # shaded band
        fig.add_vrect(
            x0=ev["start"],
            x1=ev["end"],
            fillcolor=ev["color"],
            line_width=0,
            layer="below",
        )

        # centered label just above the series
        fig.add_annotation(
            x=ev["mid"],
            y=max_y * 1.02,
            text=f"<b>{ev['name']}</b>",
            showarrow=False,
            yanchor="bottom",
            align="center",
            font=dict(size=11, color="black"),
        )

        # invisible marker for detailed hover tooltip
        fig.add_trace(
            go.Scatter(
                x=[ev["mid"]],
                y=[max_y],
                mode="markers",
                marker=dict(size=10, opacity=0),
                showlegend=False,
                hovertemplate=f"<b>{ev['name']}</b><br>{ev['explanation']}<extra></extra>",
            )
        )

    # Layout + animation (dark theme)
    countries_str = ", ".join(selected_countries)
    fig.update_layout(
        template=TEMPLATE,
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Value",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(t=100, l=40, r=40, b=80),
        title=dict(
            text=f"Macroeconomic Indicators – {countries_str}",
            x=0.0,
            xanchor="left",
        ),
        transition=dict(duration=500, easing="cubic-in-out"),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ─────────────────────────────────────────
    # KEY EVENT IMPACT ANALYSIS (BAR CHART)
    # ─────────────────────────────────────────
    st.subheader("Key event impact analysis")

    event_names = [ev["name"] for ev in key_events]
    selected_event_name = st.selectbox(
        "Choose a key event to compare its impact (before vs after):",
        event_names,
    )

    window_months = st.slider(
        "Months before/after event to compare:",
        min_value=3,
        max_value=24,
        value=12,
        step=3,
    )

    selected_event = next(ev for ev in key_events if ev["name"] == selected_event_name)

    pre_start = selected_event["start"] - pd.DateOffset(months=window_months)
    pre_end = selected_event["start"]

    post_start = selected_event["end"]
    post_end = selected_event["end"] + pd.DateOffset(months=window_months)

    # Restrict to current filters and event window
    pre_df = df_filtered[(df_filtered["Date"] >= pre_start) & (df_filtered["Date"] < pre_end)]
    post_df = df_filtered[(df_filtered["Date"] > post_start) & (df_filtered["Date"] <= post_end)]

    if pre_df.empty or post_df.empty:
        st.info(
            "Not enough data in the selected time range to compare before and "
            f"after **{selected_event_name}**. Try widening the main time range."
        )
    else:
        rows = []
        for country in selected_countries:
            for metric in selected_metrics:
                pre_val = pre_df.loc[pre_df["Country"] == country, metric].mean()
                post_val = post_df.loc[post_df["Country"] == country, metric].mean()

                if pd.isna(pre_val) and pd.isna(post_val):
                    continue

                change = post_val - pre_val
                pct_change = np.nan
                if pre_val not in (0, np.nan):
                    pct_change = (change / pre_val) * 100

                rows.append(
                    {
                        "Country": country,
                        "Metric": metric,
                        "Average before": pre_val,
                        "Average after": post_val,
                        "Change": change,
                        "Change (%)": pct_change,
                    }
                )

        if rows:
            impact_df = pd.DataFrame(rows)

            impact_fig = px.bar(
                impact_df,
                x="Country",
                y="Change",
                color="Metric",
                barmode="group",
                template=TEMPLATE,
                title=f"Average change in selected metrics before vs after {selected_event_name}",
                height=350,
            )
            st.plotly_chart(impact_fig, use_container_width=True)

            # Optional detail table

            impact_df.index = impact_df.index
            
            st.dataframe(
                impact_df.style.format(
                    {
                        "Average before": "{:.2f}",
                        "Average after": "{:.2f}",
                        "Change": "{:.2f}",
                        "Change (%)": "{:.1f}%",
                    }
                ),
                use_container_width=True,
            )
        else:
            st.info(
                f"No data available to compute impact for **{selected_event_name}** "
                "with the current selections."
            )

    # ─────────────────────────────────────────
    # KEY EVENT EXPLANATIONS
    # ─────────────────────────────────────────
    with st.expander("Key event explanations"):
        for ev in key_events:
            st.markdown(
                f"""
    ### **{ev['name']} ({ev['start'].year}–{ev['end'].year})**
    {ev['explanation']}
    """
            )

if __name__ == "__main__":
    render_event_page()

