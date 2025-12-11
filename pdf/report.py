"""
Script used for generating PDF report from dashboard.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

#--------------
# PDF Generator
#--------------
def render_matplotlib_plot(df_view, selected_mines, out_path="chart_matplotlib.png"):
    """
    Saving chart using matplotlib.
    """
    plt.figure(figsize=(10, 4))

    for m in selected_mines:
        plt.plot(df_view["Date"], df_view[m], label=m)

    plt.xlabel("Date")
    plt.ylabel("Output")
    plt.title("Mining Output (matplotlib export)")
    plt.legend()
    plt.tight_layout()

    plt.savefig(out_path, dpi=150)
    plt.close()

    return out_path


def generate_full_pdf(df, stats_df, anomalies, events, selected_mines,
                      out_dir="pdf_reports", chart_type="line", trend_degree=1):
    """
    Creates a PDF report compliant with the task requirements.
    """

    os.makedirs(out_dir, exist_ok=True)

    # Save plot as PNG (render matplotlib from df and selected_mines)
    plot_path = os.path.join(out_dir, "chart.png")
    try:
        render_matplotlib_plot(df.loc[:, ["Date"] + selected_mines], selected_mines, out_path=plot_path)
    except Exception as e:
        # fallback: try to render whatever we can
        try:
            render_matplotlib_plot(df, selected_mines, out_path=plot_path)
        except Exception as e2:
            raise RuntimeError(f"Failed to export plot to PNG: {e}; fallback error: {e2}")

    # Prepare PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Mining Output Analysis Report", ln=1, align="C")

    # metadata about chart
    pdf.ln(4)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Chart type: {chart_type}; Trend degree: {trend_degree}", ln=1)

    # Statistics section
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Basic Statistics", ln=1)
    pdf.set_font("Arial", "", 10)

    # print stats for selected mines + total (if present)
    for mine in selected_mines + (["Total"] if "Total" in stats_df.index else []):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, f"{mine}", ln=1)
        pdf.set_font("Arial", "", 10)
        try:
            row = stats_df.loc[mine]
            pdf.cell(0, 6, f"  mean: {row.get('mean', float('nan')):.3f}", ln=1)
            pdf.cell(0, 6, f"  std: {row.get('std', float('nan')):.3f}", ln=1)
            pdf.cell(0, 6, f"  median: {row.get('median', float('nan')):.3f}", ln=1)
            pdf.cell(0, 6, f"  IQR: {row.get('IQR', float('nan')):.3f}", ln=1)
        except Exception:
            pdf.cell(0, 6, "  (statistics unavailable)", ln=1)
        pdf.ln(2)

    # Anomaly summary (per selected mine)
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Anomaly Detection Summary", ln=1)
    pdf.set_font("Arial", "", 10)

    for mine in selected_mines:
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, f"{mine} anomalies:", ln=1)
        pdf.set_font("Arial", "", 10)

        if mine in anomalies.columns:
            outlier_indices = anomalies[mine][anomalies[mine]].index.tolist()
        else:
            outlier_indices = []

        if not outlier_indices:
            pdf.cell(0, 6, "  No anomalies detected.", ln=1)
        else:
            for idx in outlier_indices:
                try:
                    date = pd.to_datetime(df.loc[idx, "Date"]).strftime("%Y-%m-%d")
                except Exception:
                    date = str(df.loc[idx, "Date"])
                pdf.cell(0, 6, f"  {date}", ln=1)
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
