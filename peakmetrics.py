import streamlit as st
import pandas as pd
import plotly.express as px


# -------------------------
# PeakMetrics V1
# -------------------------

st.set_page_config(
    page_title="PeakMetrics",
    layout="wide"
)


st.title("PeakMetrics 🏃")
st.subheader("Running Performance Dashboard")


# -------------------------
# Example Running Data
# -------------------------

data = {
    "Date": [
        "2026-07-01",
        "2026-07-03",
        "2026-07-05",
        "2026-07-06",
        "2026-07-08"
    ],

    "Distance": [
        8.0,
        10.0,
        16.0,
        7.5,
        10.2
    ],

    "Time": [
        58,
        70,
        112,
        54,
        70
    ],

    "Avg HR": [
        138,
        145,
        146,
        140,
        142
    ],

    "Power": [
        300,
        315,
        320,
        305,
        318
    ]
}


df = pd.DataFrame(data)

df["Date"] = pd.to_datetime(df["Date"])


# Calculate pace

df["Pace"] = df["Time"] / df["Distance"]



# -------------------------
# Dashboard Metrics
# -------------------------

total_miles = df["Distance"].sum()

total_time = df["Time"].sum()

average_hr = df["Avg HR"].mean()

average_pace = df["Pace"].mean()



col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "Weekly Mileage",
    f"{total_miles:.1f} mi"
)

col2.metric(
    "Training Time",
    f"{total_time/60:.1f} hrs"
)

col3.metric(
    "Average HR",
    f"{average_hr:.0f}"
)

col4.metric(
    "Average Pace",
    f"{average_pace:.2f} min/mi"
)



# -------------------------
# Run History
# -------------------------

st.header("Runs")

st.dataframe(df)



# -------------------------
# Mileage Graph
# -------------------------

st.header("Mileage Trend")


fig = px.line(
    df,
    x="Date",
    y="Distance",
    markers=True,
    title="Daily Mileage"
)

st.plotly_chart(fig)



# -------------------------
# Heart Rate Efficiency
# -------------------------

st.header("Heart Rate Efficiency")


df["Efficiency"] = df["Distance"] / df["Avg HR"]


fig2 = px.line(
    df,
    x="Date",
    y="Efficiency",
    markers=True,
    title="Running Efficiency"
)

st.plotly_chart(fig2)