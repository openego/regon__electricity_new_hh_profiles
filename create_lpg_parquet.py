"""
Create a single Parquet file from all LPG mfh CSV profiles.

Each CSV contains one household profile at 15-min resolution for year 2011
(35,040 rows, `Electricity_HH1` column in kWh). This script:
  1. Reads every CSV in MFH_DIR
  2. Resamples 15-min → 1-hour by summing 4 intervals
  3. Converts kWh → Wh (× 1000)
  4. Names each column {HH_TYPE}a{id:05d} with sequential IDs per type
     (HH_TYPE is either CHR__ or CHS__, e.g. CHR01, CHS04)
  5. Concatenates all columns and saves as Parquet

Output shape: (8760, N_profiles)
Output index: DatetimeIndex hourly 2011-01-01 … 2011-12-31
"""

import re
from pathlib import Path

import pandas as pd

# ============================================================================
# Configuration
# ============================================================================

MFH_DIR = Path(__file__).resolve().parent / "generated_profiles" / "mfh"
OUTPUT_FILE = Path(__file__).resolve().parent / "hh_el_load_profiles_lpg.parquet"

# Filename pattern: resulting_profiles_{HH_TYPE}_..._seed_{N}_all.csv
FILENAME_RE = re.compile(r"^resulting_profiles_((?:CHR|CHS)\d+)_.*_all\.csv$")

# ============================================================================
# Collect and sort files
# ============================================================================

csv_files = sorted(MFH_DIR.glob("resulting_profiles_*.csv"))
print(f"Found {len(csv_files)} CSV files in {MFH_DIR}")

# ============================================================================
# Read, resample, rename
# ============================================================================

series_list = []
type_counters: dict[str, int] = {}

for i, path in enumerate(csv_files):
    match = FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(f"Unexpected filename: {path.name}")

    hh_type = match.group(1)  # e.g. "CHR01" or "CHS04"

    series = pd.read_csv(path, index_col=0, parse_dates=True)["Electricity_HH1"]

    # Resample 15-min → 1-hour (sum 4 intervals) and convert kWh → Wh
    series = series.resample("h").sum() * 1000

    if len(series) != 8760:
        raise ValueError(f"Expected 8760 hourly steps, got {len(series)}: {path.name}")

    # Assign column name with sequential ID per household type
    idx = type_counters.get(hh_type, 0)
    type_counters[hh_type] = idx + 1
    series.name = f"{hh_type}a{idx:05d}"

    series_list.append(series)

    if (i + 1) % 500 == 0 or (i + 1) == len(csv_files):
        print(f"  processed {i + 1}/{len(csv_files)} files ...")

# ============================================================================
# Assemble and save
# ============================================================================

print(f"\nAssembling DataFrame ({len(series_list)} profiles) ...")
df_out = pd.concat(series_list, axis=1)

print(f"Shape: {df_out.shape}")
print(f"Index: {df_out.index[0]} … {df_out.index[-1]}")
print("Household types and profile counts:")
for hh_type, count in sorted(type_counters.items()):
    print(f"  {hh_type}: {count}")

print(f"\nSaving to {OUTPUT_FILE} ...")
df_out.to_parquet(OUTPUT_FILE)
print("Done.")