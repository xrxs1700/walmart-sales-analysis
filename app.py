"""Dash dashboard for the Walmart Sales project.

Run with:
    python app.py
Then open http://127.0.0.1:8050/ in a browser.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

DATA_PATH = Path(__file__).resolve().parent / "walmart_sales.csv"

# Holiday lookup copied from the notebook so the dashboard stays in sync.
HOLIDAY_DATES: Dict[str, List[str]] = {
    "Super Bowl": ["2010-02-12", "2011-02-11", "2012-02-10"],
    "Labor Day": ["2010-09-10", "2011-09-09", "2012-09-07"],
    "Thanksgiving": ["2010-11-26", "2011-11-25"],
    "Christmas": ["2010-12-31", "2011-12-30"],
}


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and clean the Walmart weekly sales data."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    df = df.sort_values(["Store", "Date"]).reset_index(drop=True)
    df["Weekly_Sales"] = df["Weekly_Sales"].round(2)
    df["Temperature"] = df["Temperature"].round().astype(int)
    df["Fuel_Price"] = df["Fuel_Price"].round(2)
    df["CPI"] = df["CPI"].round(3)
    df["Unemployment"] = df["Unemployment"].round(3)
    df["Is_Holiday_Week"] = np.where(df["Holiday_Flag"] == 1, "Holiday Weeks", "Non-Holiday Weeks")

    holiday_lookup = {
        pd.to_datetime(date): name  # keep datetime objects for fast map
        for name, dates in HOLIDAY_DATES.items()
        for date in dates
    }
    df["Holiday_Name"] = df["Date"].map(holiday_lookup)
    return df


analysis_df = load_data()

holiday_sales = (
    analysis_df[analysis_df["Holiday_Flag"] == 1]
    .assign(Holiday_Name=lambda d: d["Holiday_Name"].fillna("Other Holiday"))
    .groupby("Holiday_Name", as_index=False)["Weekly_Sales"]
    .agg(average_sales="mean", median_sales="median", observations="count")
    .sort_values("average_sales", ascending=False)
)

store_stats = (
    analysis_df.groupby("Store")
    .agg(
        avg_unemployment=("Unemployment", "mean"),
        avg_weekly_sales=("Weekly_Sales", "mean"),
        avg_cpi=("CPI", "mean"),
    )
    .reset_index()
)

fuel_sales = (
    analysis_df.groupby("Date", as_index=False)
    .agg(
        total_weekly_sales=("Weekly_Sales", "sum"),
        avg_fuel_price=("Fuel_Price", "mean"),
    )
    .sort_values("Date")
)

summary_cards = [
    {
        "label": "Store-Weeks",
        "value": f"{analysis_df.shape[0]:,}",
        "subtext": "rows after cleaning",
    },
    {
        "label": "Stores",
        "value": f"{analysis_df['Store'].nunique()}",
        "subtext": "unique locations",
    },
    {
        "label": "Average Weekly Sales",
        "value": f"${analysis_df['Weekly_Sales'].mean():,.0f}",
        "subtext": "per store-week",
    },
    {
        "label": "Date Range",
        "value": f"{analysis_df['Date'].min():%b %Y} – {analysis_df['Date'].max():%b %Y}",
        "subtext": "full coverage",
    },
]


def build_holiday_fig() -> go.Figure:
    fig = px.bar(
        holiday_sales,
        x="Holiday_Name",
        y="average_sales",
        text="observations",
        color="average_sales",
        color_continuous_scale="Blues",
    )
    fig.update_traces(marker_line_color="black", marker_line_width=0.5)
    fig.update_layout(
        coloraxis_showscale=False,
        yaxis_title="Average Weekly Sales ($)",
        xaxis_title="",
        title="Holiday Weeks with the Largest Sales Lift",
    )
    return fig


def build_store_fig(selected_store: int | None) -> go.Figure:
    fig = px.scatter(
        store_stats,
        x="avg_unemployment",
        y="avg_weekly_sales",
        size="avg_cpi",
        hover_data={"Store": True, "avg_cpi": ":.2f"},
        labels={
            "avg_unemployment": "Avg. Unemployment (%)",
            "avg_weekly_sales": "Avg. Weekly Sales ($)",
            "avg_cpi": "Avg. CPI",
        },
        title="Store-Level View: Does Unemployment Suppress Sales?",
    )
    fig.update_traces(marker=dict(color="#4C78A8", opacity=0.65, line=dict(width=0)))

    if selected_store is not None and selected_store in store_stats["Store"].values:
        row = store_stats[store_stats["Store"] == selected_store].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=[row["avg_unemployment"]],
                y=[row["avg_weekly_sales"]],
                mode="markers+text",
                text=[f"Store {selected_store}"],
                textposition="bottom center",
                marker=dict(
                    size=16,
                    color="crimson",
                    symbol="star",
                    line=dict(color="black", width=1),
                ),
                name=f"Store {selected_store}",
                showlegend=False,
            )
        )
    return fig


def build_cpi_fig(flag: str) -> go.Figure:
    if flag == "holiday":
        subset = analysis_df[analysis_df["Holiday_Flag"] == 1]
        title = "Holiday Weeks"
    elif flag == "non_holiday":
        subset = analysis_df[analysis_df["Holiday_Flag"] == 0]
        title = "Non-Holiday Weeks"
    else:
        subset = analysis_df
        title = "All Weeks"

    fig = px.scatter(
        subset,
        x="CPI",
        y="Weekly_Sales",
        color="Is_Holiday_Week",
        color_discrete_map={"Holiday Weeks": "#E45756", "Non-Holiday Weeks": "#4C78A8"},
        opacity=0.6,
        title=f"CPI vs. Weekly Sales · {title}",
    )
    fig.update_layout(
        legend_title="Week Type",
        xaxis_title="Consumer Price Index",
        yaxis_title="Weekly Sales ($)",
    )

    if not subset.empty:
        coeffs = np.polyfit(subset["CPI"], subset["Weekly_Sales"], 1)
        x_vals = np.linspace(subset["CPI"].min(), subset["CPI"].max(), 50)
        y_vals = coeffs[0] * x_vals + coeffs[1]
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                name="Trendline",
                line=dict(color="black", dash="dash"),
                showlegend=True,
            )
        )
    return fig


def build_fuel_fig() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=fuel_sales["Date"],
            y=fuel_sales["avg_fuel_price"],
            name="Avg Fuel Price ($)",
            mode="lines",
            line=dict(color="#1F77B4"),
            yaxis="y1",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=fuel_sales["Date"],
            y=fuel_sales["total_weekly_sales"] / 1_000_000,
            name="Total Weekly Sales (millions $)",
            mode="lines",
            line=dict(color="#FF7F0E"),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Fuel Price vs. Total Weekly Sales",
        xaxis_title="Date",
        yaxis=dict(title="Fuel Price ($)", showgrid=False),
        yaxis2=dict(
            title="Total Weekly Sales (millions $)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


app = Dash(__name__)
app.title = "Walmart Sales Dashboard"

app.layout = html.Div(
    [
        html.H1("Walmart Sales Dashboard"),
        html.P(
            "Interactive view of the cleaned dataset used in the portfolio notebook. "
            "Explore how holidays, regional unemployment, CPI, and fuel prices interact with weekly revenue."
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3(card["value"]),
                        html.P(card["label"]),
                        html.Small(card["subtext"]),
                    ],
                    className="summary-card",
                )
                for card in summary_cards
            ],
            className="summary-grid",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H4("Holiday Performance"),
                        dcc.Graph(
                            id="holiday-sales",
                            figure=build_holiday_fig(),
                            config={"displayModeBar": False},
                        ),
                    ],
                    className="chart-card",
                ),
                html.Div(
                    [
                        html.H4("Store Sensitivity to Unemployment"),
                        dcc.Dropdown(
                            id="store-dropdown",
                            options=[
                                {"label": f"Store {store}", "value": int(store)}
                                for store in sorted(store_stats["Store"].unique())
                            ],
                            value=int(store_stats["Store"].iloc[0]),
                            clearable=False,
                        ),
                        dcc.Graph(id="store-unemployment"),
                    ],
                    className="chart-card",
                ),
            ],
            className="chart-grid",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H4("CPI vs. Weekly Sales"),
                        dcc.RadioItems(
                            id="cpi-filter",
                            options=[
                                {"label": "All weeks", "value": "all"},
                                {"label": "Holiday weeks only", "value": "holiday"},
                                {"label": "Non-holiday weeks", "value": "non_holiday"},
                            ],
                            value="all",
                            inline=True,
                        ),
                        dcc.Graph(id="cpi-scatter"),
                    ],
                    className="chart-card",
                ),
                html.Div(
                    [
                        html.H4("Fuel Price vs. Total Sales"),
                        dcc.Graph(
                            id="fuel-sales",
                            figure=build_fuel_fig(),
                        ),
                    ],
                    className="chart-card",
                ),
            ],
            className="chart-grid",
        ),
        html.Footer(
            [
                html.Small(
                    "Built with Dash · Data source: Kaggle Walmart Sales · "
                    "Notebook + dashboard by Iris Shtutman"
                )
            ],
            style={"marginTop": "2rem", "textAlign": "center"},
        ),
    ],
    className="page",
)


@app.callback(Output("store-unemployment", "figure"), Input("store-dropdown", "value"))
def update_store_chart(selected_store: int) -> go.Figure:
    return build_store_fig(selected_store)


@app.callback(Output("cpi-scatter", "figure"), Input("cpi-filter", "value"))
def update_cpi_chart(flag: str) -> go.Figure:
    return build_cpi_fig(flag)

# Simple inline CSS so the dashboard looks decent without external assets.
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                background: #f5f5f5;
            }
            .page {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem 1.5rem 3rem 1.5rem;
            }
            h1 {
                margin-bottom: 0.25rem;
            }
            .summary-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }
            .summary-card {
                background: white;
                border-radius: 8px;
                padding: 1rem;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
            }
            .summary-card h3 {
                margin: 0;
                font-size: 1.5rem;
            }
            .summary-card p {
                margin: 0.25rem 0 0 0;
                font-weight: 500;
            }
            .summary-card small {
                color: #6b7280;
            }
            .chart-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 1.5rem;
                margin-bottom: 1.5rem;
            }
            .chart-card {
                background: white;
                border-radius: 8px;
                padding: 1rem;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
            }
            .chart-card h4 {
                margin-top: 0;
            }
            footer small {
                color: #6b7280;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


if __name__ == "__main__":
    app.run(debug=True)
