"""
Quantity comparison between SAS and PBI tabs for matched Order.Line values.

This script reads the same workbook used for the Order.Line comparison and
performs a row-by-row join on the normalized Order.Line values.  It then
checks whether the numeric quantities (order, ship, first ship) are equal
between the two systems and reports any differences.

Usage:
    python quantity_comparison.py

Configuration variables at the top of the file can be modified as needed.
"""

import pandas as pd
import sys

# ============= CONFIGURATION =============
INPUT_FILE = r"C:\Users\Chris Gilson\OneDrive\Documents\Dupuis Analytics\OmniMax\SAS vs PBI Order Line Comparison.xlsx"
SAS_TAB = "SAS"
PBI_TAB = "PBI"
COLUMN_NAME = "Order.Line"
# standardized names we use internally when comparing
COMPARE_COLUMNS = ["order_quantity", "ship_quantity", "first_ship_quantity"]
# mappings from actual column names in each tab to our standardized names
SAS_COLUMN_MAP = {
    "Order Qty": "order_quantity",
    "1st Ship Qty": "first_ship_quantity",
    "Ship Qty": "ship_quantity",
    # order.line already matches but ensure it's present
    "Order.Line": "Order.Line"
}
PBI_COLUMN_MAP = {
    "Order Qty": "order_quantity",
    "First Ship Qty": "first_ship_quantity",
    "Ship Qty": "ship_quantity",
    "Order.Line": "Order.Line"
}

OUTPUT_TAB = "Quantity Differences"
# =========================================


def normalize_order_line(value):
    """Ensure order line is text with at least two decimals (same as prior script)."""
    if pd.isna(value):
        return None
    value_str = str(value).strip()
    try:
        value_float = float(value_str)
        if value_float == int(value_float):
            return f"{int(value_float)}.00"
        elif value_float * 10 == int(value_float * 10):
            return f"{value_float:.1f}0"
        elif value_float * 100 == int(value_float * 100):
            return f"{value_float:.2f}"
        else:
            return f"{value_float:.3f}"
    except:
        return value_str


def load_and_prepare(sheet_name, label):
    df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)
    # choose the correct mapping based on label
    col_map = SAS_COLUMN_MAP if label == "SAS" else PBI_COLUMN_MAP
    # ensure required columns exist
    missing = [col for col in col_map if col not in df.columns]
    if missing:
        raise KeyError(f"Missing expected columns in {label} tab: {missing}")
    # rename the numeric quantity columns to our standard names
    rename_map = {orig: std for orig, std in col_map.items() if std != "Order.Line"}
    df = df.rename(columns=rename_map)
    # normalize order line
    if COLUMN_NAME not in df.columns:
        raise KeyError(f"Column '{COLUMN_NAME}' not found in {label} tab after renaming")
    df[COLUMN_NAME] = df[COLUMN_NAME].apply(normalize_order_line)
    return df


def main():
    try:
        sas = load_and_prepare(SAS_TAB, "SAS")
        pbi = load_and_prepare(PBI_TAB, "PBI")
    except Exception as exc:
        print("Error reading or preparing sheets:", exc)
        sys.exit(1)

    # only keep the relevant comparison columns plus key
    sas_small = sas[[COLUMN_NAME] + COMPARE_COLUMNS].copy()
    pbi_small = pbi[[COLUMN_NAME] + COMPARE_COLUMNS].copy()

    # rename columns so they don't collide after merge
    sas_small = sas_small.rename(columns={col: f"sas_{col}" for col in COMPARE_COLUMNS})
    pbi_small = pbi_small.rename(columns={col: f"pbi_{col}" for col in COMPARE_COLUMNS})

    merged = pd.merge(sas_small, pbi_small, on=COLUMN_NAME, how="inner")
    print(f"Total matched order lines: {len(merged):,}")

    # detect differences
    diffs = []
    for col in COMPARE_COLUMNS:
        sas_col = f"sas_{col}"
        pbi_col = f"pbi_{col}"
        diff_flag = merged[sas_col] != merged[pbi_col]
        mismatch = merged[diff_flag][[COLUMN_NAME, sas_col, pbi_col]]
        if not mismatch.empty:
            diffs.append((col, mismatch))
            print(f"Found {len(mismatch)} mismatches in '{col}'")

    if not diffs:
        print("All quantities tie out between SAS and PBI for matched order lines.")
    else:
        # optionally write to excel with summary sheet
        try:
            with pd.ExcelWriter(INPUT_FILE.replace('.xlsx', '_quantity_diff.xlsx')) as writer:
                for col, df in diffs:
                    df.to_excel(writer, sheet_name=col.replace('_', ' ').title(), index=False)
            print("Mismatch details written to", INPUT_FILE.replace('.xlsx', '_quantity_diff.xlsx'))
        except Exception as exc:
            print("Error writing output file:", exc)


if __name__ == '__main__':
    main()
