# %%
"""
CAA Registration Change Validator (Optimized)

-------------------------------------------

Purpose:
This script validates that the geofencing + CAA membership script is working correctly
by finding aircraft that changed their CAA Registration status (Y/N) during a given month.

Why this matters:
If the term date logic is working properly, we should see some aircraft flip from Y to N
(or N to Y) mid-month when their membership expires or begins. Finding these transitions
proves the daily membership file lookup and term date validation are functioning.

What it does:
1. Reads the output CSV from the geofencing script
2. Groups flights by aircraft tail sign
3. Sorts by arrival date within each aircraft
4. Identifies any aircraft where CAA Registration changed during the month
5. Exports a summary report showing before/after status and transition dates

Usage:
Just update input_file_name to the month you want to validate.

Performance:
Uses vectorized pandas operations - processes 500k rows in ~2-3 seconds.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import pandas as pd
from datetime import datetime


# =============================================================================
# USER INPUTS (edit these each month)
# =============================================================================

user = 'Chris Gilson'

# INPUT FILE PATH AND NAME (output from geofencing script)
input_file_path      = f'C:/Users/{user}/OneDrive/Documents/Dupuis Analytics/CAA/WingX_Data/Geofenced & CAA Tails mapped/'
input_file_name      = 'wx_flight_data_February_2026_geofenced_with_caa_registration'
input_file_path_full = f'{input_file_path}{input_file_name}.csv'

# OUTPUT FILE PATH AND NAME (validation report)
output_file_path      = f'C:/Users/{user}/OneDrive/Documents/Dupuis Analytics/CAA/WingX_Data/'
output_file_name      = f'{input_file_name}_CAA_changes_validation'
output_file_path_full = f'{output_file_path}{output_file_name}.csv'

# Column names (should match the geofencing script output)
COL_TAILSIGN     = "aircraft_tailsign"
COL_ARRIVAL_DATE = "arrival_date_time_utc"
COL_CAA_FLAG     = "CAA Registration (Y/N)"


# =============================================================================
# MAIN SCRIPT
# =============================================================================

print(f"Reading input file: {input_file_path_full}")
df = pd.read_csv(input_file_path_full)

# Parse the arrival date
df[COL_ARRIVAL_DATE] = pd.to_datetime(df[COL_ARRIVAL_DATE], errors='coerce')

# Sort by tailsign and arrival date
df = df.sort_values([COL_TAILSIGN, COL_ARRIVAL_DATE]).reset_index(drop=True)

print(f"\nTotal flights: {len(df):,}")
print(f"Unique aircraft: {df[COL_TAILSIGN].nunique():,}")

print("\nAnalyzing CAA Registration changes (vectorized)...")

# Create a shift column to compare each flight with the previous flight for the same aircraft
df['prev_status'] = df.groupby(COL_TAILSIGN)[COL_CAA_FLAG].shift(1)
df['prev_date'] = df.groupby(COL_TAILSIGN)[COL_ARRIVAL_DATE].shift(1)

# Find rows where status changed (current != previous)
status_changed = (df[COL_CAA_FLAG] != df['prev_status']) & df['prev_status'].notna()

# Get only the rows where changes occurred
changes_df = df[status_changed].copy()

if len(changes_df) > 0:
    # Build the results dataframe
    results_df = pd.DataFrame({
        'Aircraft': changes_df[COL_TAILSIGN],
        'Change Type': changes_df['prev_status'] + ' → ' + changes_df[COL_CAA_FLAG],
        'Before Status': changes_df['prev_status'],
        'After Status': changes_df[COL_CAA_FLAG],
        'Transition Date': changes_df[COL_ARRIVAL_DATE],
    })
    
    # Add flight counts
    total_flights = df.groupby(COL_TAILSIGN).size()
    results_df['Total Flights This Month'] = results_df['Aircraft'].map(total_flights)
    
    # Sort by transition date
    results_df = results_df.sort_values('Transition Date').reset_index(drop=True)
    
    print(f"\n{'='*80}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"\nAircraft with CAA Registration changes during the month: {results_df['Aircraft'].nunique()}")
    print(f"Total transitions found: {len(results_df)}")
    print(f"\nBreakdown by change type:")
    print(results_df['Change Type'].value_counts().to_string())
    
    print(f"\n{'='*80}")
    print(f"SAMPLE OF CHANGES (first 10):")
    print(f"{'='*80}")
    print(results_df.head(10).to_string(index=False))
    
    # Save full results
    print(f"\nSaving full results to: {output_file_path_full}")
    results_df.to_csv(output_file_path_full, index=False)
    
    print(f"\n✓ Validation complete! Found {results_df['Aircraft'].nunique()} aircraft with status changes.")
    print(f"  This indicates the term date validation logic is working properly.")
    
else:
    print(f"\n{'='*80}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"\nNo aircraft changed CAA Registration status during this month.")
    print(f"This could mean:")
    print(f"  - All memberships were stable (no expirations or new starts)")
    print(f"  - The data covers a short time period")
    print(f"  - There may be an issue with the term date logic (review membership files)")

print(f"\n{'='*80}")
print("Script complete!")
print(f"{'='*80}")