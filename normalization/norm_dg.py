#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize Districtgenerator profiles to 1 Mio kWh annual consumption.

- Loads all xlsx files from districtgenerator/demands (sheet "elec")
- Sums all buildings per hour
- Creates datetime index for 2011
- Normalizes to 1,000,000 kWh annual consumption
- Saves as CSV
"""

import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path.home() / "Dokumente" / "new_hh_profiles"
DG_DIR = BASE_DIR / "districtgenerator" / "demands"
OUTPUT_PATH = BASE_DIR / "districtgenerator_normalized_1mio.csv"


def load_and_combine_profiles(dg_dir):
    """Load all xlsx profiles (elec sheet) and sum them together."""
    xlsx_files = sorted(dg_dir.glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(f"No xlsx files found in {dg_dir}")

    print(f"Found {len(xlsx_files)} xlsx files")

    # Load elec sheet from each file
    all_values = []
    for i, xlsx_file in enumerate(xlsx_files):
        df = pd.read_excel(xlsx_file, sheet_name="elec")
        all_values.append(df.iloc[:, 0].values)
        if (i + 1) % 100 == 0:
            print(f"  Loaded {i + 1}/{len(xlsx_files)} files...")

    print("Combining profiles...")
    # Stack all arrays and sum per hour
    import numpy as np
    stacked = np.column_stack(all_values)
    print(f"  Stacked shape: {stacked.shape}")

    summed = stacked.sum(axis=1)
    print(f"  Summed shape: {summed.shape}")

    # Create datetime index for 2011 (hourly)
    index = pd.date_range(start="2011-01-01", periods=len(summed), freq="h")
    series = pd.Series(summed, index=index)

    return series


def normalize_to_1mio(series):
    """Normalize to 1,000,000 kWh annual consumption."""
    # Values are in Wh, convert to kWh first
    series_kwh = series / 1000
    annual_sum = series_kwh.sum()
    print(f"Original annual sum: {annual_sum:,.2f} kWh")

    # Scale factor to reach 1,000,000 kWh
    scale_factor = 1_000_000 / annual_sum
    normalized = series_kwh * scale_factor

    print(f"Scale factor: {scale_factor:.6f}")
    print(f"Normalized annual sum: {normalized.sum():,.2f} kWh")

    return normalized


def main():
    print("=" * 60)
    print("Normalizing Districtgenerator profiles to 1 Mio kWh")
    print("=" * 60)

    # Load and combine
    summed = load_and_combine_profiles(DG_DIR)

    # Normalize to 1 Mio kWh
    normalized = normalize_to_1mio(summed)

    # Create DataFrame with proper column name
    result = pd.DataFrame({
        "electricity_kwh": normalized
    })
    result.index.name = "timestamp"

    # Verify
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