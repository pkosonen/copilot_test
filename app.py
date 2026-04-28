from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from gridle_client import GridleApiError, GridleClient, MeasurementQuery


DEFAULT_API_KEY = "rtD5RveEp41L1rB6F4v572QnKrWKiIg86Vln2qCz"


load_dotenv()

DEFAULT_METRICS = [
    "grid_power_kw",
    "house_power_kw",
    "solar_power_kw",
    "battery_power_kw",
    "state_of_charge_percent",
    "spot_price_cents_per_kwh",
]


def combine_date_time(day: date, selected_time: time) -> datetime:
    local_timezone = datetime.now().astimezone().tzinfo
    return datetime.combine(day, selected_time, tzinfo=local_timezone)


@st.cache_data(ttl=60, show_spinner=False)
def load_dataframe(api_key: str, start_time: datetime | None, end_time: datetime | None) -> pd.DataFrame:
    client = GridleClient(api_key=api_key)
    rows = client.fetch_measurements(MeasurementQuery(start_time=start_time, end_time=end_time))
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["period_start"] = pd.to_datetime(frame["period_start"])
    frame["period_end"] = pd.to_datetime(frame["period_end"])
    frame = frame.sort_values("period_start")
    return frame


def app_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

            :root {
                --paper: #f7f2e8;
                --ink: #111111;
                --panel: rgba(255, 251, 245, 0.82);
            }

            html, body, [class*="css"] {
                font-family: 'Space Grotesk', sans-serif;
                color: var(--ink);
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(217, 93, 57, 0.18), transparent 28%),
                    radial-gradient(circle at bottom right, rgba(28, 110, 140, 0.12), transparent 30%),
                    linear-gradient(180deg, #f8f4eb 0%, #efe3d1 100%);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
            }

            .hero {
                background: linear-gradient(135deg, rgba(255,255,255,0.75), rgba(240,195,166,0.55));
                border: 1px solid rgba(17,17,17,0.08);
                border-radius: 24px;
                padding: 1.75rem 1.5rem;
                backdrop-filter: blur(10px);
                box-shadow: 0 24px 64px rgba(17, 17, 17, 0.08);
                margin-bottom: 1rem;
            }

            .hero h1 {
                font-size: clamp(2rem, 4vw, 3.8rem);
                line-height: 0.95;
                margin-bottom: 0.75rem;
            }

            .metric-card {
                background: var(--panel);
                border: 1px solid rgba(17,17,17,0.08);
                border-radius: 18px;
                padding: 1rem;
            }

            .tiny {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.9rem;
                color: rgba(17,17,17,0.72);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Gridle Residential Client", page_icon=":zap:", layout="wide")
    app_styles()

    st.markdown(
        """
        <section class="hero">
            <div class="tiny">Gridle Residential API client</div>
            <h1>Inspect live home energy data without leaving the browser.</h1>
            <p>Query the public measurements endpoint, compare power flows over time, and inspect the raw 5-minute series returned by the API.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Connection")
        api_key = st.text_input(
            "API key",
            value=os.getenv("GRIDLE_API_KEY", DEFAULT_API_KEY),
            type="password",
        )
        use_range = st.toggle("Use custom time range", value=False)

        start_time = None
        end_time = None
        if use_range:
            today = date.today()
            default_start = today - timedelta(days=1)
            start_day = st.date_input("Start date", value=default_start, max_value=today)
            start_clock = st.time_input("Start time", value=time(hour=0, minute=0))
            end_day = st.date_input("End date", value=today, max_value=today)
            end_clock = st.time_input("End time", value=time(hour=23, minute=55))
            start_time = combine_date_time(start_day, start_clock)
            end_time = combine_date_time(end_day, end_clock)

        st.caption("The API returns 5-minute aggregated data and enforces a 31-day maximum range.")
        refresh = st.button("Fetch measurements", type="primary", use_container_width=True)

    if not api_key:
        st.info("Provide an API key in the sidebar or set GRIDLE_API_KEY in your shell environment.")
        return

    if use_range and start_time and end_time and start_time >= end_time:
        st.error("Start time must be earlier than end time.")
        return

    if use_range and start_time and end_time and end_time - start_time > timedelta(days=31):
        st.error("The API supports a maximum time range of 31 days.")
        return

    if not refresh and "frame" not in st.session_state:
        return

    if refresh or "frame" not in st.session_state:
        try:
            with st.spinner("Loading measurements from Gridle..."):
                st.session_state.frame = load_dataframe(api_key, start_time, end_time)
        except GridleApiError as exc:
            st.error(f"API request failed: {exc}")
            return
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
            return

    frame = st.session_state.frame
    if frame.empty:
        st.warning("The API returned no measurements for the selected range.")
        return

    numeric_columns = [
        column
        for column in frame.columns
        if column not in {"period_start", "period_end"} and pd.api.types.is_numeric_dtype(frame[column])
    ]
    default_selection = [metric for metric in DEFAULT_METRICS if metric in numeric_columns] or numeric_columns[:3]

    metrics = st.multiselect("Metrics", options=numeric_columns, default=default_selection)
    if not metrics:
        st.warning("Select at least one metric to render the chart.")
        return

    latest = frame.iloc[-1]
    cards = st.columns(min(4, len(metrics)))
    for index, metric in enumerate(metrics[:4]):
        with cards[index]:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            value = latest[metric]
            st.metric(metric, value=f"{value:.3f}" if pd.notna(value) else "n/a")
            st.markdown("</div>", unsafe_allow_html=True)

    chart_frame = frame[["period_start", *metrics]].melt(
        id_vars="period_start", var_name="metric", value_name="value"
    )
    line_chart = px.line(
        chart_frame,
        x="period_start",
        y="value",
        color="metric",
        template="plotly_white",
        line_shape="spline",
    )
    line_chart.update_layout(
        height=540,
        legend_title_text="",
        margin=dict(l=12, r=12, t=16, b=12),
        hovermode="x unified",
    )
    st.plotly_chart(line_chart, use_container_width=True)

    with st.expander("Raw data"):
        st.dataframe(frame, use_container_width=True)


if __name__ == "__main__":
    main()
