"""
Compare shipping and order quantities along with OTIF metrics between SAS and PBI tabs.

This script handles Order.Lines that appear multiple times by comparing the complete
set of rows for each Order.Line rather than doing a 1-to-1 merge.

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
    """Ensure order line is text with at least two decimals (same as quantity_comparison.py)."""
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
    
    # Report duplicate statistics
    duplicates = df[df.duplicated(subset=[COLUMN_NAME], keep=False)]
    if not duplicates.empty:
        dup_count = duplicates[COLUMN_NAME].nunique()
        print(f"{label} tab: {len(df):,} total rows, {dup_count:,} Order.Lines appear multiple times")
    else:
        print(f"{label} tab: {len(df):,} total rows, all Order.Lines unique")
    
    return df


def create_row_signature(row, columns):
    """Create a unique signature for a row based on specified columns"""
    parts = [str(row[col]) if pd.notna(row[col]) else 'NULL' for col in columns]
    return '|'.join(parts)


def find_set_differences(sas, pbi):
    """
    Find Order.Lines where the complete set of rows differs between SAS and PBI.
    Returns a dictionary with Order.Line as key and details about the mismatch.
    """
    # Create row signatures for each dataframe
    sas['_signature'] = sas.apply(lambda row: create_row_signature(row, COMPARE_COLUMNS), axis=1)
    pbi['_signature'] = pbi.apply(lambda row: create_row_signature(row, COMPARE_COLUMNS), axis=1)
    
    # Get unique signatures per Order.Line for each system
    sas_sets = sas.groupby(COLUMN_NAME)['_signature'].apply(set).to_dict()
    pbi_sets = pbi.groupby(COLUMN_NAME)['_signature'].apply(set).to_dict()
    
    # Find all unique Order.Lines across both systems
    all_order_lines = set(sas_sets.keys()) | set(pbi_sets.keys())
    
    mismatches = {}
    
    for order_line in all_order_lines:
        sas_set = sas_sets.get(order_line, set())
        pbi_set = pbi_sets.get(order_line, set())
        
        if sas_set != pbi_set:
            # Found a mismatch - gather details
            only_in_sas = sas_set - pbi_set
            only_in_pbi = pbi_set - sas_set
            
            mismatches[order_line] = {
                'only_in_sas': only_in_sas,
                'only_in_pbi': only_in_pbi,
                'sas_row_count': len(sas_set),
                'pbi_row_count': len(pbi_set)
            }
    
    return mismatches


def create_detailed_report(mismatches, sas, pbi):
    """
    Create detailed Excel sheets showing the actual rows for each mismatched Order.Line
    """
    report_data = []
    
    for order_line in sorted(mismatches.keys()):
        # Get all rows for this Order.Line from both systems
        sas_rows = sas[sas[COLUMN_NAME] == order_line][COMPARE_COLUMNS].copy()
        pbi_rows = pbi[pbi[COLUMN_NAME] == order_line][COMPARE_COLUMNS].copy()
        
        # Add source column
        sas_rows['Source'] = 'SAS'
        pbi_rows['Source'] = 'PBI'
        
        # Add Order.Line column
        sas_rows[COLUMN_NAME] = order_line
        pbi_rows[COLUMN_NAME] = order_line
        
        # Combine
        combined = pd.concat([sas_rows, pbi_rows], ignore_index=True)
        combined = combined[[COLUMN_NAME, 'Source'] + COMPARE_COLUMNS]
        
        report_data.append(combined)
    
    if report_data:
        return pd.concat(report_data, ignore_index=True)
    else:
        return pd.DataFrame()


def main():
    try:
        print("Loading data...")
        sas = load_and_prepare(SAS_TAB, "SAS")
        pbi = load_and_prepare(PBI_TAB, "PBI")
    except Exception as exc:
        print("Error preparing sheets:", exc)
        sys.exit(1)

    print("\nComparing row sets for each Order.Line...")
    mismatches = find_set_differences(sas, pbi)
    
    if not mismatches:
        print("✓ No differences found - all Order.Lines have matching row sets between SAS and PBI.")
        return
    
    print(f"\n✗ Found {len(mismatches):,} Order.Lines with different row sets between SAS and PBI")
    
    # Show summary of first few mismatches
    print("\nFirst 10 mismatched Order.Lines:")
    for i, (order_line, details) in enumerate(sorted(mismatches.items())[:10]):
        print(f"  {order_line}: SAS has {details['sas_row_count']} rows, PBI has {details['pbi_row_count']} rows")
    
    # Create detailed report
    print("\nGenerating detailed report...")
    detailed_report = create_detailed_report(mismatches, sas, pbi)
    
    # Write to Excel
    out_file = INPUT_FILE.replace('.xlsx', OUTPUT_SUFFIX)
    try:
        with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
            # Summary sheet
            summary = pd.DataFrame([
                {'Order.Line': ol, 
                 'SAS_Rows': d['sas_row_count'], 
                 'PBI_Rows': d['pbi_row_count']}
                for ol, d in sorted(mismatches.items())
            ])
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed sheet with all rows
            detailed_report.to_excel(writer, sheet_name='Detailed Comparison', index=False)
        
        print(f"\n✓ Results written to: {out_file}")
        print(f"  - 'Summary' sheet: List of {len(mismatches)} mismatched Order.Lines")
        print(f"  - 'Detailed Comparison' sheet: All rows for mismatched Order.Lines")
        
    except Exception as exc:
        print("Failed to write output:", exc)


if __name__ == '__main__':
    main()