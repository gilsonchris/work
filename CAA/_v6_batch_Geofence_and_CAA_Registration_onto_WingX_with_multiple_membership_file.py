# %%
"""
WingX geofence mapping + daily CAA membership flag (with term date validation)
BATCH PROCESSING VERSION

-------------------------------------------

The big picture
You have two data sources that you want to combine: WingX flight landing data, and CAA membership records. 
The script's job is to take every landing, figure out where exactly the plane landed (which FBO), 
and whether that plane was a paid CAA member on the day it landed. 
The result is one clean output file with all of that information merged together.

Step by step

Reading the landings data. The script starts by loading the WingX CSV, which has one row per landing. 
Each row has a tail sign, a timestamp, and GPS coordinates for where the plane shut down. 
It cleans up the tail signs immediately (strips spaces, makes everything uppercase) 
so that "n123ab" and "N123AB " don't get treated as different aircraft later. 

Figuring out where each plane landed (the geofence part). 
The GPS shutdown coordinates are just numbers — latitude and longitude. 
The script converts those into actual map points, then overlays them against the FBO shapefile, 
which is a map of polygon boundaries drawn around each FBO ramp. 
If a landing point falls inside one of those polygons, the script stamps that landing with the FBO's name and details. 
This is the spatial join. Landings that don't fall inside any polygon just get blanks for those fields.

Finding the right membership file. 
For each landing, the script looks at the arrival date and goes to the membership folder to find the right daily extract.
It tries to find a file from that exact date first. If there's no file for that date, it walks backwards in time 
— yesterday, day before, and so on — until it finds one. 
It never looks forward, because a file from the future would reflect members 
who might not have been signed up yet on the actual landing date.

Checking membership. 
Once it has the right file, it looks at both sheets inside it —
the Full Members sheet and the Trial Members sheet — and builds a combined list of every tail sign that appears in either one. 
Then it checks: does this landing's tail sign appear on that list? If yes, the landing gets a "Y" for CAA Registration. 
If not, it gets an "N."

Writing the output. 
Everything — the original landing data, the FBO geofence match, and the Y/N membership flag — 
gets written out to a single CSV file.

Why it's built this way
The reason for the daily membership file logic (rather than one master membership file) is that 
membership changes over time — planes join, planes leave. 
By matching each landing to the membership snapshot from that specific date, 
we get an accurate picture of who was actually a member when they landed, 
not just whether they're a member today. 
The backwards-lookup rule handles gaps in the data without ever making assumptions about the future.

------------------------------------------------

What this script does (high level):
1) Reads the WingX flight CSV.
2) Converts lat/long to a GeoDataFrame (points).
3) Spatially joins those points to the FBO geofence shapefile (adds FBO fields to each flight row).
4) For each flight, finds the right daily membership file by looking at the arrival date,
   then walking backwards in time until a file is found.
5) Checks BOTH membership sheets (Full + Trial) and flags aircraft_tailsign as Y or N.
   A tail gets Y only if:
     - It appears in that date's membership file, AND
     - The arrival date falls within its Term Start Date and Term End Date
   This catches edge cases like weekend landings after a membership has expired.
6) All original columns and data types are preserved exactly as they came in.
7) Exports the final joined dataset to CSV.

Performance note:
The CAA flag step uses vectorized pandas operations (a merge + column comparisons) rather
than row-by-row Python loops. On 600k rows this runs in under a minute instead of 20-40 minutes.
The logic is identical — just expressed as column math instead of a for loop.

This script prioritizes readability and easy monthly edits.
"""

# =============================================================================
# STEP ONE: imports
# =============================================================================

import os
from datetime import datetime
import glob

import geopandas as gpd
import pandas as pd


# =============================================================================
# USER INPUTS (edit these each month)
# =============================================================================

# Optional: some GeoPandas/GDAL setups on Windows need GDAL_DATA set.
# If the current environment already works without it, you can delete this line.
os.environ["GDAL_DATA"] = r"C:\Users\Chris Gilson\anaconda3\envs\geo_env\Library\share\gdal"

# Change user inputs
user = 'Chris Gilson'

# =============================================================================
# BATCH PROCESSING MODE
# =============================================================================
# Set to True to process ALL files in the Raw folder
# Set to False to process just one specific file (set input_file_name below)
BATCH_MODE = False

# WingX INPUT FILE PATH (folder containing WingX CSV files)
input_file_path = f'C:/Users/{user}/OneDrive/Documents/Dupuis Analytics/CAA/WingX_Data/Raw/'

# Single file mode: specify the file to process
input_file_name = 'wx_flight_data_February_2026'  # Only used if BATCH_MODE = False

# WingX CSV column names used by this script
COL_TAILSIGN     = "aircraft_tailsign"
COL_ARRIVAL_DATE = "arrival_date_time_utc"
COL_LON          = "arrival_airport_shutdown_longitude"
COL_LAT          = "arrival_airport_shutdown_latitude"

# Geofence file path and name - Shapefile needs to be remade/renamed each time FBO descriptions change
geofence_file_path      = f'C:/Users/{user}/OneDrive/Documents/Dupuis Analytics/CAA/Geofence project/'
geofence_version        = 'FBOs_current'   # e.g. 'FBOs_named_7_25_2025'
geofence_file_path_full = f'{geofence_file_path}{geofence_version}.shp'

# Columns from the shapefile to carry into the output (edit if schema changes)
FBO_KEEP_COLUMNS = ["Index", "Destinatio", "Destinat_1", "geometry"]

# CAA MEMBERSHIP FOLDER (daily extracts)
# Files in this folder are expected to start with a date: MM.DD.YYYY
#   e.g. "10.17.2025 Active Membership.xlsx"
membership_base_path   = f'C:/Users/{user}/OneDrive/Documents/Dupuis Analytics/CAA/CAA_membership/'
membership_year        = 'all'          # dump everything into this folder
membership_folder      = f'{membership_base_path}{membership_year}/'
membership_date_format = "%m.%d.%Y"     # edit if the filename date format ever changes

# Sheet names inside each membership Excel file
membership_sheet_full  = "Active Full Member Aircraft"
membership_sheet_trial = "Active Trial Aircraft"

# Column names inside the membership sheets
REG_COL_AIRCRAFT_OLD = "Aircraft"              # used before Dec 2025
REG_COL_AIRCRAFT_NEW = "Related Aircraft"      # used from Dec 2025 onward
REG_COL_AIRCRAFT = "Aircraft"                  # standardized name used internally
REG_COL_START    = "Term Start Date"
REG_COL_END      = "Term End Date"

# OUTPUT FILE PATH
output_file_path = f'C:/Users/{user}/OneDrive/Documents/Dupuis Analytics/CAA/WingX_Data/'

# The new column we will add to the output
OUT_COL_CAA_FLAG = "CAA Registration (Y/N)"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def list_membership_files_by_date(folder, date_format):
    """
    Scan the membership folder and return a dict:
        { pandas.Timestamp(date) : full_file_path }

    Only files whose names BEGIN with a parsable date in the given format
    are included. All other files are skipped silently.
    """
    mapping = {}

    for fname in os.listdir(folder):
        if not fname.lower().endswith((".xlsx", ".xls")):
            continue

        # The date is the first token in the filename (before a space or underscore)
        raw_date = fname.split(" ")[0].split("_")[0]

        try:
            parsed_date = datetime.strptime(raw_date, date_format).date()
        except ValueError:
            continue   # Filename doesn't match expected date format; skip it

        ts = pd.to_datetime(parsed_date).normalize()
        mapping[ts] = os.path.join(folder, fname)

    return mapping


def build_arrival_to_membership_date_lookup(flight_dates, membership_date_map):
    """
    For each unique arrival date in flight_dates, find the most recent
    membership file date that is ON or BEFORE the arrival date (never after).

    Returns a Series:  arrival_date -> membership_date (or NaT if none found)
    """
    unique_arrivals = (
        pd.Series(flight_dates.dropna().unique())
        .sort_values()
        .reset_index(drop=True)
        .rename("arrival_date")
        .to_frame()
    )

    membership_dates = (
        pd.Series(sorted(membership_date_map.keys()))
        .rename("membership_date")
        .to_frame()
    )

    if membership_dates.empty:
        return pd.Series(pd.NaT, index=unique_arrivals["arrival_date"])

    # merge_asof finds the last membership_date <= arrival_date (backward direction)
    merged = pd.merge_asof(
        left=unique_arrivals,
        right=membership_dates,
        left_on="arrival_date",
        right_on="membership_date",
        direction="backward",
    )

    return merged.set_index("arrival_date")["membership_date"]


def load_all_membership_records(membership_date_map, needed_dates):
    """
    Load only the membership files actually needed (dates that appear in the data).
    Reads both the Full and Trial sheets from each file, stacks them together,
    and returns ONE combined DataFrame with a membership_date column added.

    This single combined DataFrame is what makes the vectorized merge possible —
    instead of looping row by row, we can join flights to this table all at once.

    Returns:
        DataFrame with columns: [membership_date, Aircraft, Term Start Date, Term End Date]
    """
    all_records = []

    for m_date in needed_dates:
        path = membership_date_map[m_date]
        print(f"  Reading membership file for {m_date.date()}: {os.path.basename(path)}")

        sheets_data = []
        for sheet in [membership_sheet_full, membership_sheet_trial]:
            try:
                # First, try the new column name
                try:
                    df = pd.read_excel(path, sheet_name=sheet, usecols=[REG_COL_AIRCRAFT_NEW, REG_COL_START, REG_COL_END])
                    df = df.rename(columns={REG_COL_AIRCRAFT_NEW: REG_COL_AIRCRAFT})  # standardize to internal name
                except ValueError:
                    # If new column doesn't exist, fall back to old column name
                    df = pd.read_excel(path, sheet_name=sheet, usecols=[REG_COL_AIRCRAFT_OLD, REG_COL_START, REG_COL_END])
                    df = df.rename(columns={REG_COL_AIRCRAFT_OLD: REG_COL_AIRCRAFT})  # standardize to internal name
                
                sheets_data.append(df)
            except Exception as e:
                print(f"    Warning: could not read sheet '{sheet}': {e}")

        if not sheets_data:
            continue

        combined = pd.concat(sheets_data, ignore_index=True)

        # Normalize tail and parse term dates
        combined[REG_COL_AIRCRAFT] = combined[REG_COL_AIRCRAFT].astype(str).str.strip().str.upper()
        combined[REG_COL_START]    = pd.to_datetime(combined[REG_COL_START], errors="coerce").dt.normalize()
        combined[REG_COL_END]      = pd.to_datetime(combined[REG_COL_END],   errors="coerce").dt.normalize()

        # Tag each record with which membership snapshot it came from
        combined["membership_date"] = m_date

        all_records.append(combined)

    if not all_records:
        return pd.DataFrame(columns=["membership_date", REG_COL_AIRCRAFT, REG_COL_START, REG_COL_END])

    return pd.concat(all_records, ignore_index=True)


def process_single_file(input_file_path_full, output_file_path_full, fbo_gdf, membership_date_map):
    """
    Process a single WingX CSV file through the complete pipeline.
    Returns True if successful, False if error.
    """
    try:
        # =============================================================================
        # STEP TWO: read the flight CSV and build a GeoDataFrame
        # =============================================================================

        print(f"  Reading flight CSV: {os.path.basename(input_file_path_full)}")
        flight_df = pd.read_csv(input_file_path_full)

        # Preserve original values for both columns we will normalize, so we can restore
        # them exactly before export — no changes to the original data in the output
        flight_df["_original_tailsign"]     = flight_df[COL_TAILSIGN]
        flight_df["_original_arrival_date"] = flight_df[COL_ARRIVAL_DATE]

        # Normalize tailsigns for matching (strip whitespace, uppercase)
        flight_df[COL_TAILSIGN] = (
            flight_df[COL_TAILSIGN]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # Parse arrival datetime and create a date-only column for membership matching
        flight_df[COL_ARRIVAL_DATE]    = pd.to_datetime(flight_df[COL_ARRIVAL_DATE], errors="coerce")
        flight_df["arrival_date_only"] = flight_df[COL_ARRIVAL_DATE].dt.normalize()

        # Stable row id so we can safely re-join after spatial operations
        flight_df["landing_row_id"] = flight_df.index

        # Build GeoDataFrame from lat/long
        flight_gdf = gpd.GeoDataFrame(
            flight_df,
            geometry=gpd.points_from_xy(flight_df[COL_LON], flight_df[COL_LAT]),
            crs="EPSG:4326",
        )

        # =============================================================================
        # STEP FOUR: spatial join (attach FBO fields to each flight record)
        # =============================================================================

        print(f"  Running spatial join...")
        joined_gdf = gpd.sjoin(
            flight_gdf,
            fbo_gdf,
            how="left",
            predicate="intersects",
        )

        # =============================================================================
        # STEP FIVE: daily membership logic + CAA flag (vectorized)
        # =============================================================================

        # For each unique arrival date, find the most recent membership file on or before that date
        arrival_to_membership_date = build_arrival_to_membership_date_lookup(
            joined_gdf["arrival_date_only"],
            membership_date_map,
        )

        # Map each flight row to its resolved membership_date
        joined_gdf["membership_date"] = joined_gdf["arrival_date_only"].map(arrival_to_membership_date)

        # Only load membership files that are actually referenced in the data
        needed_dates = set(joined_gdf["membership_date"].dropna().unique())
        print(f"  Loading {len(needed_dates)} unique membership file(s)...")
        all_membership_df = load_all_membership_records(membership_date_map, needed_dates)

        print(f"  Computing CAA Registration flags (vectorized)...")

        # Pull just the columns we need from the flights for this merge
        flights_for_merge = joined_gdf[["landing_row_id", "membership_date", COL_TAILSIGN, "arrival_date_only"]].copy()

        # Merge flights against all membership records on membership_date + tailsign
        merged = flights_for_merge.merge(
            all_membership_df,
            how="left",
            left_on=["membership_date", COL_TAILSIGN],
            right_on=["membership_date", REG_COL_AIRCRAFT],
        )

        # Apply the four term date cases as vectorized boolean columns
        has_start   = merged[REG_COL_START].notna()
        has_end     = merged[REG_COL_END].notna()
        has_arrival = merged["arrival_date_only"].notna()

        # Case 1: Both dates present — arrival must fall within the term
        case_both   = has_arrival & has_start & has_end & \
                      (merged["arrival_date_only"] >= merged[REG_COL_START]) & \
                      (merged["arrival_date_only"] <= merged[REG_COL_END])

        # Case 2: Only end date — arrival must be on or before end
        case_no_start = has_arrival & ~has_start & has_end & \
                        (merged["arrival_date_only"] <= merged[REG_COL_END])

        # Case 3: Only start date — arrival must be on or after start
        case_no_end   = has_arrival & has_start & ~has_end & \
                        (merged["arrival_date_only"] >= merged[REG_COL_START])

        # Case 4: Neither date — presence in the file is sufficient
        case_no_dates = has_arrival & ~has_start & ~has_end & merged[REG_COL_AIRCRAFT].notna()

        # A row is a valid active membership if ANY of the four cases is true
        within_term = case_both | case_no_start | case_no_end | case_no_dates

        # Collapse to one Y/N per original landing_row_id
        any_match = within_term.groupby(merged["landing_row_id"]).any()

        # Map back onto the full joined GeoDataFrame
        joined_gdf[OUT_COL_CAA_FLAG] = (
            joined_gdf["landing_row_id"]
            .map(any_match)
            .fillna(False)
            .map({True: "Y", False: "N"})
        )

        # =============================================================================
        # STEP SIX: restore original columns and export to CSV
        # =============================================================================

        # Restore both original columns exactly as they came in
        joined_gdf[COL_TAILSIGN]     = joined_gdf["_original_tailsign"]
        joined_gdf[COL_ARRIVAL_DATE] = joined_gdf["_original_arrival_date"]

        # Drop all internal working columns before export
        joined_gdf = joined_gdf.drop(columns=[
            "_original_tailsign",
            "_original_arrival_date",
            "arrival_date_only",
            "membership_date",
        ])

        print(f"  Writing output CSV: {os.path.basename(output_file_path_full)}")
        joined_gdf.to_csv(output_file_path_full, index=False)
        print(f"  ✓ Success!\n")
        
        return True
        
    except Exception as e:
        print(f"  ✗ ERROR processing file: {e}\n")
        return False


# =============================================================================
# MAIN EXECUTION
# =============================================================================

print("="*80)
print("WingX Geofence + CAA Membership Processing")
print("="*80)

# Load geofence shapefile once (reused for all files)
print(f"\nReading geofence shapefile: {geofence_file_path_full}")
fbo_gdf = gpd.read_file(geofence_file_path_full)
fbo_gdf = fbo_gdf[FBO_KEEP_COLUMNS].copy()
fbo_gdf = fbo_gdf.set_crs(epsg=4326)

# Load membership file mapping once (reused for all files)
print(f"\nScanning membership folder: {membership_folder}")
membership_date_map = list_membership_files_by_date(membership_folder, membership_date_format)
print(f"  Found {len(membership_date_map)} membership file(s).")

if not membership_date_map:
    print("  Warning: No membership files found. All CAA flags will be 'N'.")

# Determine which files to process
if BATCH_MODE:
    # Find all CSV files matching the pattern
    pattern = os.path.join(input_file_path, 'wx_flight_data_*.csv')
    files_to_process = glob.glob(pattern)
    
    if not files_to_process:
        print(f"\nNo files found matching pattern: {pattern}")
        print("Exiting.")
    else:
        print(f"\n{'='*80}")
        print(f"BATCH MODE: Found {len(files_to_process)} file(s) to process")
        print(f"{'='*80}\n")
        
        success_count = 0
        fail_count = 0
        
        for i, input_file_path_full in enumerate(files_to_process, 1):
            # Extract the base filename without extension
            base_name = os.path.basename(input_file_path_full).replace('.csv', '')
            output_file_name = f'{base_name}_geofenced_with_caa_registration'
            output_file_path_full = f'{output_file_path}{output_file_name}.csv'
            
            print(f"[{i}/{len(files_to_process)}] Processing: {os.path.basename(input_file_path_full)}")
            
            if process_single_file(input_file_path_full, output_file_path_full, fbo_gdf, membership_date_map):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"{'='*80}")
        print(f"BATCH COMPLETE")
        print(f"{'='*80}")
        print(f"Successfully processed: {success_count} file(s)")
        print(f"Failed: {fail_count} file(s)")
        print(f"{'='*80}")
else:
    # Single file mode
    input_file_path_full = f'{input_file_path}{input_file_name}.csv'
    output_file_name = f'{input_file_name}_geofenced_with_caa_registration'
    output_file_path_full = f'{output_file_path}{output_file_name}.csv'
    
    print(f"\n{'='*80}")
    print(f"SINGLE FILE MODE")
    print(f"{'='*80}\n")
    
    process_single_file(input_file_path_full, output_file_path_full, fbo_gdf, membership_date_map)
    
    print(f"{'='*80}")
    print("Processing complete!")
    print(f"{'='*80}")