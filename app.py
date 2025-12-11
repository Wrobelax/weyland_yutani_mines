"""
Main script for running the app.
"""

import streamlit as st
import pandas as pd


from data.loader import load_data, load_events
from analysis.stats import calculate_stats, detect_anomalies
from charts.plotting import create_figure
from pdf.report import generate_full_pdf

#----------------------------
# Streamlit page configurator
#----------------------------
st.set_page_config(page_title="Weyland-Yutani Mines Dashboard", layout="wide")
st.title("Weyland-Yutani Mines Dashboard")


# ----------------------------------
# Load data, events, calculate stats
# ----------------------------------
data = load_data()
st.subheader("Preview of Generated Data")
st.dataframe(data.head())

events = load_events()

stats = calculate_stats(data)


#-----------------
# Sidebar controls
#-----------------
# date range filter
min_date = data['Date'].min()
max_date = data['Date'].max()
date_range = st.sidebar.date_input("Date range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Sidebar controls
st.sidebar.header("Controls")
methods_selected = st.sidebar.multiselect("Anomaly methods", ["IQR", "z-score", "moving_avg", "grubbs"], default=["IQR", "z-score"])
z_thresh = st.sidebar.slider("z-score threshold", 2.0, 5.0, 3.0, step=0.5)
ma_window = st.sidebar.slider("MA window (days)", 3, 30, 7)
ma_pct = st.sidebar.slider("MA percent threshold", 0.05, 0.5, 0.2, step=0.01)
iqr_factor = st.sidebar.slider("IQR factor", 1.0, 3.0, 1.5, step=0.1)

all_mines = [
    col for col in data.columns
    if col not in ["Date"] and "Randomizer" not in col and pd.api.types.is_numeric_dtype(data[col])
]

selected_mines = st.sidebar.multiselect("Select mines", all_mines, default=[all_mines[0]])
if not selected_mines:
    st.warning("Select at least one mine to proceed.")
    st.stop()

chart_type = st.sidebar.selectbox("Chart type", ["line", "bar", "stacked"])
show_trend = st.sidebar.checkbox("Show polynomial trendline (single mine only)", value=True)
trend_degree = st.sidebar.selectbox("Trendline degree (1-4)", [1,2,3,4], index=0)

# compute anomalies with chosen params
anomalies = detect_anomalies(data, methods=methods_selected, z_thresh=z_thresh,
                             ma_window=ma_window, iqr_factor=iqr_factor, ma_pct=ma_pct)
# date filtering
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
mask = (data['Date'] >= start_date) & (data['Date'] <= end_date)
df_view = data.loc[mask].reset_index(drop=True)
anomalies_view = anomalies.loc[mask].reset_index(drop=True)


# ----------
# Plot chart
# ----------
fig = create_figure(
    df_view=df_view,
    anomalies_view=anomalies_view,
    selected_mines=selected_mines,
    chart_type=chart_type,
    show_trend=show_trend,
    trend_degree=trend_degree
)

st.plotly_chart(fig, width="stretch")


#-------------------------------------
#Show statistics and anomalies summary
#-------------------------------------
st.subheader("Statistics (per mine)")
display_list = selected_mines.copy()
if "Total" in stats.index and "Total" not in display_list:
    display_list = display_list + ["Total"]
st.dataframe(stats.loc[display_list])

st.subheader("Anomalies summary (count per mine in selected date range)")

anomalies_view_bool = anomalies_view.copy().astype(bool)
mine_cols_for_counts = [m for m in selected_mines if m in anomalies_view_bool.columns]

if not mine_cols_for_counts:
    st.info("No valid mine selected for anomaly summary.")
else:
    per_mine_counts = anomalies_view_bool[mine_cols_for_counts].sum().astype(int)

    sum_of_anomalies = int(per_mine_counts.sum())

    unique_anomaly_days = int(anomalies_view_bool[mine_cols_for_counts].any(axis=1).sum())

    st.table(per_mine_counts.to_frame(name='Anomaly count'))

    st.markdown(f"**Sum of anomalies (sum of per-mine counts):** {sum_of_anomalies}")
    st.markdown(f"**Unique anomaly days (at least one mine):** {unique_anomaly_days}")


# -------------
# PDF Generator
# -------------
if st.button("Generate PDF Report"):

    events_from_sheet = load_events()

    file_path = generate_full_pdf(
        df=data,
        stats_df=stats,
        anomalies=anomalies,
        events=events_from_sheet,
        selected_mines=selected_mines,
        fig=fig,
        chart_type=chart_type,
        trend_degree=trend_degree
    )
    with open(file_path, "rb") as f:
        st.download_button(
            label="Download PDF",
            data=f,
            file_name="report.pdf",
            mime="application/pdf"
        )
    st.success("PDF successfully generated. Click the button above to download.")
