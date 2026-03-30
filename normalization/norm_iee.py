#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize IEE profiles to 1 Mio kWh annual consumption.

- Loads all 100,000 profiles from HDF file using h5py (memory efficient)
- Sums all profiles per hour
- Normalizes to 1,000,000 kWh annual consumption
- Saves as CSV with 2011 timestamps
"""

import pandas as pd
import numpy as np
import h5py
from pathlib import Path

# Paths
BASE_DIR = Path.home() / "Dokumente" / "new_hh_profiles"
IEE_PATH = BASE_DIR / "hh_el_load_profiles_100k.hdf"
OUTPUT_PATH = BASE_DIR / "iee_normalized_1mio.csv"

# Process in chunks to manage memory
CHUNK_SIZE = 10000


def load_and_sum_profiles(iee_path):
    """Load all profiles from HDF and sum them together, processing in chunks."""
    print(f"Opening HDF file: {iee_path}")

    with h5py.File(iee_path, 'r') as f:
        # Data is at hh_el_load_profiles/block0_values with shape (8760, 100000)
        dataset = f['hh_el_load_profiles']['block0_values']
        n_hours, n_profiles = dataset.shape
        print(f"  Dataset shape: {n_hours} hours x {n_profiles} profiles")

        # Sum profiles in chunks to manage memory
        print(f"  Processing in chunks of {CHUNK_SIZE} profiles...")
        summed = np.zeros(n_hours)

        for start in range(0, n_profiles, CHUNK_SIZE):
            end = min(start + CHUNK_SIZE, n_profiles)
            chunk = dataset[:, start:end]
            summed += chunk.sum(axis=1)
            print(f"    Processed {end}/{n_profiles} profiles...")

    # Create datetime index for 2011 (hourly)
    index = pd.date_range(start="2011-01-01", periods=n_hours, freq="h")
    series = pd.Series(summed, index=index)

    return series


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
    print("Normalizing IEE profiles to 1 Mio kWh")
    print("=" * 60)

    # Load and sum all profiles
    summed = load_and_sum_profiles(IEE_PATH)

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