"""
Script used for generating PDF report from dashboard.
"""

import os
import pandas as pd
import plotly.io as pio
from fpdf import FPDF

#--------------
# PDF Generator
#--------------
def generate_full_pdf(
    df,
    stats_df,
    anomalies,
    events,
    selected_mines,
    fig,
    out_dir="pdf_reports",
):
    """
    Creates a PDF report compliant with the task requirements.
    """

    os.makedirs(out_dir, exist_ok=True)

    # Save plot as PNG
    plot_path = os.path.join(out_dir, "chart.png")
    pio.write_image(fig, plot_path, format="png", scale=2)

    # Add total stats
    total_stats = stats_df.loc["Total"]

    # Helper to fetch stat (tries stats_df first, then total_stats for "Total")
    def get_stat(mine, key):
        try:
            if mine == "Total":
                return total_stats.get(key, float("nan"))
            else:
                return float(stats_df.loc[mine, key])
        except Exception:
            return float("nan")

    # Prepare PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Mining Output Analysis Report", ln=1, align="C")

    # Statistics section
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Basic Statistics", ln=1)

    pdf.set_font("Arial", "", 10)

    for mine in selected_mines + ["Total"]:
        pdf.cell(0, 6, f"{mine} anomalies:", ln=1)

        if mine in anomalies.columns:
            outlier_indices = anomalies[mine][anomalies[mine]].index
        else:
            outlier_indices = []

        for idx in outlier_indices:
            try:
                date = pd.to_datetime(df.loc[idx, "Date"]).strftime("%Y-%m-%d")
            except Exception:
                date = str(df.loc[idx, "Date"])
            pdf.cell(0, 6, f"  {date}", ln=1)

        if len(outlier_indices) == 0:
            pdf.cell(0, 6, "  No anomalies detected.", ln=1)

        pdf.ln(3)

    # Anomaly summary (per selected mine) — use full anomalies DataFrame
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Anomaly Detection Summary", ln=1)
    pdf.set_font("Arial", "", 10)

    for mine in selected_mines:
        pdf.cell(0, 6, f"{mine} anomalies:", ln=1)
        if mine in anomalies.columns:
            outlier_indices = anomalies[mine][anomalies[mine]].index
        else:
            outlier_indices = []

        if mine not in anomalies.columns:
            outlier_indices = anomalies["Total"][anomalies["Total"]].index if "Total" in anomalies.columns else []

        for idx in outlier_indices:
            try:
                date = pd.to_datetime(df.loc[idx, "Date"]).strftime("%Y-%m-%d")
            except Exception:
                date = str(df.loc[idx, "Date"])
            pdf.cell(0, 6, f"  {date}", ln=1)

        if len(outlier_indices) == 0:
            pdf.cell(0, 6, "  No anomalies detected.", ln=1)

        pdf.ln(3)

    # Insert plot
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Data Visualization", ln=1)
    pdf.ln(3)
    try:
        pdf.image(plot_path, w=180)
    except Exception:
        pdf.cell(0, 6, "  (Failed to insert chart image)", ln=1)

    # Event Sections
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "4. Spike / Drop Events", ln=1)
    pdf.set_font("Arial", "", 10)

    if not events:
        pdf.cell(0, 6, "No events configured.", ln=1)
    else:
        for i, ev in enumerate(events, start=1):
            pdf.ln(5)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 6, f"Event {i}", ln=1)
            pdf.set_font("Arial", "", 10)
            # try to format date nicely
            try:
                date_str = pd.to_datetime(ev["date"]).strftime("%Y-%m-%d")
            except Exception:
                date_str = str(ev["date"])
            pdf.cell(0, 6, f"Date: {date_str}", ln=1)
            pdf.cell(0, 6, f"Duration: {ev.get('duration', '')} days", ln=1)
            pdf.cell(0, 6, f"Factor: {ev.get('factor', '')}", ln=1)
            pdf.cell(0, 6, f"Probability: {ev.get('prob', ev.get('probability', ''))}", ln=1)
            pdf.ln(2)
            pdf.multi_cell(0, 5, "Event impact shape: Gaussian bell curve applied across duration.")
            pdf.ln(2)

    # Save final file
    file_path = os.path.join(out_dir, "report.pdf")
    pdf.output(file_path)

    return file_path