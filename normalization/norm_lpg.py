#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize PyLPG profiles to 1 Mio kWh annual consumption.

- Loads all 1000 profiles from sfh directory
- Sums all profiles per timestamp
- Resamples to hourly values
- Normalizes to 1,000,000 kWh annual consumption
- Saves as CSV with 2011 timestamps
"""

import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path.home() / "Dokumente" / "new_hh_profiles"
FZJ_DIR = BASE_DIR / "pylpg" / "generated_profiles" / "sfh"
OUTPUT_PATH = BASE_DIR / "pylpg_normalized_1mio.csv"


def load_and_combine_profiles(fzj_dir):
    """Load all CSV profiles and sum them together."""
    csv_files = sorted(fzj_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {fzj_dir}")

    print(f"Found {len(csv_files)} CSV files")

    # Load and combine all CSVs
    dfs = []
    for i, csv_file in enumerate(csv_files):
        df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
        dfs.append(df)
        if (i + 1) % 100 == 0:
            print(f"  Loaded {i + 1}/{len(csv_files)} files...")

    print("Combining profiles...")
    combined = pd.concat(dfs, axis=1)
    print(f"  Combined shape: {combined.shape}")

    # Sum all profiles per timestamp
    print("Summing all profiles per timestamp...")
    summed = combined.sum(axis=1)
    print(f"  Summed shape: {summed.shape}")

    return summed


def resample_to_hourly(series):
    """Resample to hourly values (sum of 15-min intervals)."""
    print("Resampling to hourly...")
    hourly = series.resample("h").sum()
    print(f"  Hourly shape: {hourly.shape}")
    return hourly


def normalize_to_1mio(series):
    """Normalize to 1,000,000 kWh annual consumption."""
    annual_sum = series.sum()
    print(f"Original annual sum: {annual_sum:,.2f} kWh")

    # Scale factor to reach 1,000,000 kWh
    scale_factor = 1_000_000 / annual_sum
    normalized = series * scale_factor

    print(f"Scale factor: {scale_factor:.6f}")
    print(f"Normalized annual sum: {normalized.sum():,.2f} kWh")

    return normalized


def main():
    print("=" * 60)
    print("Normalizing PyLPG profiles to 1 Mio kWh")
    print("=" * 60)

    # Load and combine
    summed = load_and_combine_profiles(FZJ_DIR)

    # Resample to hourly
    hourly = resample_to_hourly(summed)

    # Normalize to 1 Mio kWh
    normalized = normalize_to_1mio(hourly)

    # Create DataFrame with proper column name
    result = pd.DataFrame({
        "electricity_kwh": normalized
    })
    result.index.name = "timestamp"

    # Verify it's 2011 data with 8760 hours
    print(f"\nResult:")
    print(f"  Date range: {result.index[0]} to {result.index[-1]}")
    print(f"  Number of hours: {len(result)}")
    print(f"  Annual sum: {result['electricity_kwh'].sum():,.0f} kWh")

    # Save to CSV
    result.to_csv(OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")
    print(f"File size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()