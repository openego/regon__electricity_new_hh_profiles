#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize SLP (Standardlastprofil) H25 to 1 Mio kWh annual consumption.

- Loads H25 sheet from the SLP file
- Applies dynamization function: x = x0 * f(t)
  where f(t) = -3.92E-10*t⁴ + 3.20E-7*t³ - 7.02E-5*t² + 2.10E-3*t + 1.24
  and t = day of year (1-365)
- Uses German holiday calendar for 2011 to assign day types
- Resamples to hourly values
- Normalizes to 1,000,000 kWh annual consumption
- Saves as CSV with 2011 timestamps
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
BASE_DIR = Path.home() / "Dokumente" / "new_hh_profiles"
SLP_PATH = BASE_DIR / "Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.ods"
OUTPUT_PATH = BASE_DIR / "slp_normalized_1mio.csv"


def get_german_holidays_2011():
    """
    German public holidays for 2011 (nationwide).
    Returns set of dates.
    """
    holidays = [
        "2011-01-01",  # Neujahr
        "2011-04-22",  # Karfreitag
        "2011-04-24",  # Ostersonntag
        "2011-04-25",  # Ostermontag
        "2011-05-01",  # Tag der Arbeit
        "2011-06-02",  # Christi Himmelfahrt
        "2011-06-12",  # Pfingstsonntag
        "2011-06-13",  # Pfingstmontag
        "2011-10-03",  # Tag der Deutschen Einheit
        "2011-12-25",  # 1. Weihnachtstag
        "2011-12-26",  # 2. Weihnachtstag
    ]
    return set(pd.to_datetime(holidays).date)


def dynamization_factor(day_of_year):
    """
    Calculate dynamization factor for a given day of year.
    f(t) = -3.92E-10*t⁴ + 3.20E-7*t³ - 7.02E-5*t² + 2.10E-3*t + 1.24
    """
    t = day_of_year
    return (-3.92e-10 * t**4 + 3.20e-7 * t**3 - 7.02e-5 * t**2 + 2.10e-3 * t + 1.24)


def get_day_type(date, holidays):
    """
    Determine day type for a given date.
    Returns: 'WT' (Werktag), 'SA' (Samstag), 'FT' (Sonn-/Feiertag)
    """
    if date.date() in holidays or date.dayofweek == 6:  # Sunday or holiday
        return 'FT'
    elif date.dayofweek == 5:  # Saturday
        return 'SA'
    else:  # Monday-Friday (not holiday)
        return 'WT'


def load_slp_data(slp_path):
    """
    Load SLP H25 data and parse the structure.
    Returns dict with monthly profiles for each day type.
    """
    print(f"Loading SLP data from: {slp_path}")

    # Load raw data
    df = pd.read_excel(slp_path, sheet_name="H25", header=None)

    # Structure:
    # Row 0: Header text
    # Row 1: Empty
    # Row 2: Month dates (2012-01-01, etc.) in columns 2+
    # Row 3: Day types (WT, SA, FT) in columns 2+
    # Row 4+: Values (96 rows for 15-min intervals)
    # Column 1: Time ranges (00:00-00:15, etc.)

    # Extract time slots (96 quarter-hours per day)
    time_slots = df.iloc[4:100, 1].values
    print(f"  Found {len(time_slots)} time slots")

    # Parse month/day-type combinations from header rows
    # Columns 2-37 contain the data (12 months × 3 day types = 36 columns)
    profiles = {}

    for col in range(2, 38):
        month_date = df.iloc[2, col]  # Row 2 has month dates
        day_type = df.iloc[3, col]    # Row 3 has day types

        if pd.isna(month_date) or pd.isna(day_type):
            continue

        # Extract month number from datetime
        if hasattr(month_date, 'month'):
            month = month_date.month
        elif isinstance(month_date, str) and '-' in month_date:
            month = int(month_date.split('-')[1])
        else:
            continue

        # Get values for this column (rows 4-99 = 96 values)
        values = df.iloc[4:100, col].values.astype(float)

        key = (month, str(day_type).strip())
        profiles[key] = values

    print(f"  Loaded profiles for {len(profiles)} month/day-type combinations")

    # Debug: show what we found
    months_found = sorted(set(k[0] for k in profiles.keys()))
    day_types_found = sorted(set(k[1] for k in profiles.keys()))
    print(f"  Months: {months_found}")
    print(f"  Day types: {day_types_found}")

    return profiles, time_slots


def create_yearly_profile(profiles, year=2011):
    """
    Create a full year profile at 15-minute resolution.
    Applies dynamization and uses correct day types.
    """
    print(f"Creating yearly profile for {year}...")

    holidays = get_german_holidays_2011()
    print(f"  Using {len(holidays)} German holidays")

    # Generate all 15-minute timestamps for the year
    start = pd.Timestamp(f"{year}-01-01 00:00:00")
    end = pd.Timestamp(f"{year}-12-31 23:45:00")
    timestamps = pd.date_range(start, end, freq="15min")
    print(f"  Generated {len(timestamps)} timestamps")

    values = []

    for ts in timestamps:
        month = ts.month
        day_type = get_day_type(ts, holidays)
        day_of_year = ts.dayofyear

        # Get quarter-hour index (0-95)
        quarter_hour = ts.hour * 4 + ts.minute // 15

        # Get base value from profile
        key = (month, day_type)
        if key not in profiles:
            print(f"  Warning: No profile for {key}")
            base_value = 0
        else:
            base_value = profiles[key][quarter_hour]

        # Apply dynamization
        dyn_factor = dynamization_factor(day_of_year)
        dyn_value = base_value * dyn_factor

        values.append(dyn_value)

    series = pd.Series(values, index=timestamps)
    return series


def resample_to_hourly(series):
    """Resample 15-minute values to hourly (sum)."""
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
    print("Normalizing SLP H25 profile to 1 Mio kWh")
    print("=" * 60)

    # Load SLP data
    profiles, time_slots = load_slp_data(SLP_PATH)

    # Create yearly profile with dynamization
    yearly = create_yearly_profile(profiles, year=2011)

    # Resample to hourly
    hourly = resample_to_hourly(yearly)

    # Normalize to 1 Mio kWh
    normalized = normalize_to_1mio(hourly)

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

    # Show dynamization effect
    jan_avg = result.loc["2011-01"]["electricity_kwh"].mean()
    jul_avg = result.loc["2011-07"]["electricity_kwh"].mean()
    print(f"\n  Dynamization check:")
    print(f"    January avg: {jan_avg:.2f} kWh/h")
    print(f"    July avg: {jul_avg:.2f} kWh/h")
    print(f"    Ratio Jan/Jul: {jan_avg/jul_avg:.2f}")

    # Save to CSV
    result.to_csv(OUTPUT_PATH)
    print(f"\nSaved to: {OUTPUT_PATH}")
    print(f"File size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()