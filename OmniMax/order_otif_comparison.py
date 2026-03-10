"""
Compare shipping and order quantities along with OTIF metrics between SAS and PBI tabs.

This script mirrors the pattern used previously for quantity comparisons but
adds two OTIF-related fields. Columns are normalized and discrepancies are
reported per field.

Usage:
    python order_otif_comparison.py

Adjust configuration variables at the top as needed.
"""

import pandas as pd
import sys

# ============= CONFIGURATION =============
INPUT_FILE = r"C:\Users\Chris Gilson\OneDrive\Documents\Dupuis Analytics\OmniMax\SAS vs PBI Order Line Comparison.xlsx"
SAS_TAB = "SAS"
PBI_TAB = "PBI"
COLUMN_NAME = "Order.Line"
# standardized names for all fields we will examine
COMPARE_COLUMNS = [
    "ship_quantity",
    "order_quantity",
    "otif_stp_test",
    "otif_fill_test",
    "otif_percent",
]
# mapping from original column names in each sheet to standardized keys
SAS_COLUMN_MAP = {
    "Order.Line": "Order.Line",
    "Ship Qty": "ship_quantity",
    "Order Qty": "order_quantity",
    "OTIF_STP Test": "otif_stp_test",
    "OTIF_Fill Test": "otif_fill_test",
    "OTIF %": "otif_percent",
}
PBI_COLUMN_MAP = {
    "Order.Line": "Order.Line",
    "Ship Qty": "ship_quantity",
    "Order Qty": "order_quantity",
    "OTIF STP Test": "otif_stp_test",
    "OTIF Fill Test": "otif_fill_test",
    "OTIF %": "otif_percent",
}
OUTPUT_SUFFIX = "_order_otif_diff.xlsx"
# =========================================


def normalize_order_line(value):
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    try:
        vf = float(val_str)
        if vf == int(vf):
            return f"{int(vf)}.00"
        elif vf * 10 == int(vf * 10):
            return f"{vf:.1f}0"
        elif vf * 100 == int(vf * 100):
            return f"{vf:.2f}"
        else:
            return f"{vf:.3f}"
    except:
        return val_str


def load_and_prepare(sheet_name, label):
    df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)
    col_map = SAS_COLUMN_MAP if label == "SAS" else PBI_COLUMN_MAP
    missing = [col for col in col_map if col not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in {label} tab: {missing}")
    # rename non-key columns
    rename_map = {orig: std for orig, std in col_map.items() if std != "Order.Line"}
    df = df.rename(columns=rename_map)
    if COLUMN_NAME not in df.columns:
        raise KeyError(f"Key column '{COLUMN_NAME}' missing after rename in {label} tab")
    df[COLUMN_NAME] = df[COLUMN_NAME].apply(normalize_order_line)
    return df


def main():
    try:
        sas = load_and_prepare(SAS_TAB, "SAS")
        pbi = load_and_prepare(PBI_TAB, "PBI")
    except Exception as exc:
        print("Error preparing sheets:", exc)
        sys.exit(1)

    sas_small = sas[[COLUMN_NAME] + COMPARE_COLUMNS].copy()
    pbi_small = pbi[[COLUMN_NAME] + COMPARE_COLUMNS].copy()

    sas_small = sas_small.rename(columns={c: f"sas_{c}" for c in COMPARE_COLUMNS})
    pbi_small = pbi_small.rename(columns={c: f"pbi_{c}" for c in COMPARE_COLUMNS})

    merged = pd.merge(sas_small, pbi_small, on=COLUMN_NAME, how="inner")
    print(f"Matched order lines: {len(merged):,}")

    diffs = []
    for col in COMPARE_COLUMNS:
        sas_col = f"sas_{col}"
        pbi_col = f"pbi_{col}"
        mismatch = merged[merged[sas_col] != merged[pbi_col]][[COLUMN_NAME, sas_col, pbi_col]]
        if not mismatch.empty:
            diffs.append((col, mismatch))
            print(f"{len(mismatch)} mismatches in {col}")

    if not diffs:
        print("No differences found in any compared column.")
    else:
        out_file = INPUT_FILE.replace('.xlsx', OUTPUT_SUFFIX)
        try:
            with pd.ExcelWriter(out_file) as writer:
                for col, df in diffs:
                    df.to_excel(writer, sheet_name=col.title().replace('_', ' '), index=False)
            print("Details written to", out_file)
        except Exception as exc:
            print("Failed to write output:", exc)


if __name__ == '__main__':
    main()
