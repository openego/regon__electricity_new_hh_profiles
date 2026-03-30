#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load and visualize normalized load profiles.

All profiles are normalized to 1,000,000 kWh annual consumption
and have hourly timestamps for 2011.
"""

import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# Paths
BASE_DIR = Path.home() / "Dokumente" / "new_hh_profiles"
OUTPUT_PATH = BASE_DIR / "profile_comparison.html"

# Normalized profile files
PROFILES = {
    "PyLPG": BASE_DIR / "pylpg_normalized_1mio.csv",
    "Districtgenerator": BASE_DIR / "districtgenerator_normalized_1mio.csv",
    "IEE": BASE_DIR / "iee_normalized_1mio.csv",
    "SLP H25": BASE_DIR / "slp_normalized_1mio.csv",
}

# Colors
COLORS = {
    "PyLPG": "#000080",          # Navy
    "Districtgenerator": "#228B22",  # Forest Green
    "IEE": "#FF8C00",            # Orange
    "SLP H25": "#808080",        # Grey
}


def load_profiles():
    """Load all normalized profiles into a single DataFrame."""
    print("Loading normalized profiles...")

    dfs = {}
    for name, path in PROFILES.items():
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        dfs[name] = df["electricity_kwh"]
        print(f"  {name}: {len(df)} hours, sum = {df['electricity_kwh'].sum():,.0f} kWh")

    combined = pd.DataFrame(dfs)
    return combined


def create_figure(df):
    """Create interactive Plotly figure."""

    fig = go.Figure()

    # Add trace for each profile
    for col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                name=col,
                line=dict(color=COLORS.get(col, "gray"), width=1.5),
                hovertemplate=(
                    f"<b>{col}</b><br>"
                    "Zeit: %{x}<br>"
                    "Leistung: %{y:.2f} kWh<br>"
                    "<extra></extra>"
                ),
            )
        )

    # Layout with range selector
    fig.update_layout(
        title=dict(
            text="Vergleich Haushaltslastprofile (normiert auf 1 Mio kWh/a)",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Zeit",
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1 Tag", step="day", stepmode="backward"),
                    dict(count=7, label="1 Woche", step="day", stepmode="backward"),
                    dict(count=1, label="1 Monat", step="month", stepmode="backward"),
                    dict(count=3, label="3 Monate", step="month", stepmode="backward"),
                    dict(step="all", label="Ganzes Jahr"),
                ],
                bgcolor="white",
                activecolor="lightblue",
            ),
            rangeslider=dict(visible=True, thickness=0.1),
            type="date",
        ),
        yaxis=dict(
            title="Elektrische Leistung [kWh/h]",
            autorange=True,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        template="plotly_white",
        height=700,
    )

    return fig


def main():
    print("=" * 60)
    print("Lastprofilvergleich")
    print("=" * 60)

    # Load all profiles
    df = load_profiles()
    print(f"\nCombined DataFrame: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")

    # Create figure
    print("\nCreating figure...")
    fig = create_figure(df)
    print(f"Number of traces: {len(fig.data)}")

    # Save directly with Plotly
    print(f"\nSaving to: {OUTPUT_PATH}")
    fig.write_html(OUTPUT_PATH, include_plotlyjs=True, full_html=True)

    print(f"File size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
    print(f"\nÖffnen mit: file://{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
