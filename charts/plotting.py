"""
Script used for plotting charts on dashboard.
"""

import numpy as np
import plotly.express as px
import plotly.graph_objects as go

#---------------
# Plotting logic
# --------------
def add_trendline(fig, dates, series, degree, name_prefix="Trend"):
    # Fit polynomial to y over integer x (index) to avoid date numeric issues
    x = np.arange(len(series))
    # remove NaNs
    mask = ~np.isnan(series)
    if mask.sum() < degree+1:
        return fig
    coeffs = np.polyfit(x[mask], series[mask], deg=degree)
    p = np.poly1d(coeffs)
    yfit = p(x)
    # add as scatter
    fig.add_trace(go.Scatter(x=dates, y=yfit, mode='lines', name=f"{name_prefix} (deg {degree})", line=dict(dash='dash')))
    return fig


def create_figure(df_view, anomalies_view, selected_mines, chart_type,
                  show_trend=False, trend_degree=1):
    """
    Creates a plotly figure for the dashboard.
    """

    # --- Stacked Chart ---
    if chart_type == "stacked":
        if len(selected_mines) < 2:
            # zamiast Streamlit warning – zwracamy pusty wykres z komunikatem
            fig = go.Figure()
            fig.update_layout(
                title="Select at least 2 mines for stacked chart",
                xaxis_title="Date",
                yaxis_title="Output",
            )
            return fig

        fig = px.area(
            df_view,
            x="Date",
            y=selected_mines,
            title="Stacked output (area)",
            labels={"value": "Output"}
        )

        # add outliers
        for m in selected_mines:
            out_dates = df_view["Date"][anomalies_view[m]]
            out_vals = df_view[m][anomalies_view[m]]

            if not out_dates.empty:
                fig.add_trace(go.Scatter(
                    x=out_dates,
                    y=out_vals,
                    mode='markers',
                    marker=dict(size=7),
                    name=f"Outliers {m}"
                ))

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1)
        )
        return fig

    # --- Charts for 1 or many mines (line/bar) ---
    if len(selected_mines) == 0:
        return go.Figure()

    # --- Single mine ---
    if len(selected_mines) == 1:
        mine = selected_mines[0]

        if chart_type == "line":
            fig = px.line(df_view, x="Date", y=mine, title=f"{mine} Output")
        else:
            fig = px.bar(df_view, x="Date", y=mine, title=f"{mine} Output")

        # Outliers
        out_dates = df_view["Date"][anomalies_view[mine]]
        out_vals = df_view[mine][anomalies_view[mine]]

        fig.add_trace(go.Scatter(
            x=out_dates,
            y=out_vals,
            mode="markers",
            marker=dict(color="red", size=8),
            name="Outliers"
        ))

        # Trendline
        if show_trend:
            fig = add_trendline(
                fig, df_view["Date"], df_view[mine].values,
                degree=trend_degree,
                name_prefix=f"{mine} trend"
            )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1)
        )
        return fig

    # --- Multiple mines (overlay line/bar) ---
    fig = go.Figure()

    for m in selected_mines:
        if chart_type == "line":
            fig.add_trace(go.Scatter(
                x=df_view["Date"], y=df_view[m],
                mode="lines", name=m
            ))
        else:
            fig.add_trace(go.Bar(
                x=df_view["Date"], y=df_view[m], name=m
            ))

        # outliers
        out_dates = df_view["Date"][anomalies_view[m]]
        out_vals = df_view[m][anomalies_view[m]]
        if not out_dates.empty:
            fig.add_trace(go.Scatter(
                x=out_dates,
                y=out_vals,
                mode='markers',
                marker=dict(size=6),
                name=f"Outliers {m}"
            ))

    fig.update_layout(
        title="Mine Output Comparison",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1)
    )

    return fig