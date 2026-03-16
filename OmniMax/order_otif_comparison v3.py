"""
Comprehensive OTIF validation between SAS and PBI tabs.

This script validates multiple OTIF metrics by:
1. Comparing aggregate sums between SAS and PBI
2. For metrics that don't match, drilling down to find specific Order.Lines with differences
3. Outputting each discrepancy type to its own Excel tab

Usage:
    python otif_validation.py

Adjust configuration variables at the top as needed.
"""

import pandas as pd
import sys

# ============= CONFIGURATION =============
INPUT_FILE = r"C:\Users\Chris Gilson\OneDrive\Documents\Dupuis Analytics\OmniMax\SAS vs PBI Order Line Comparison.xlsx"
SAS_TAB = "SAS"
PBI_TAB = "PBI"
COLUMN_NAME = "Order.Line"

# Metrics to validate (map from original column names to standardized names)
SAS_COLUMN_MAP = {
    "Order.Line": "Order.Line",
    "OTIF_STP Test": "otif_stp_test",
    "OTIF_Fill Test": "otif_fill_test",
    "OTIF Count": "otif_count",
    "OTIF Ship Lines": "otif_ship_lines",
}

PBI_COLUMN_MAP = {
    "Order.Line": "Order.Line",
    "OTIF STP Test": "otif_stp_test",
    "OTIF Fill Test": "otif_fill_test",
    "OTIF Count": "otif_count",
    "OTIF Ship Lines": "otif_ship_lines",
}

# Metrics to validate
METRICS = [
    "otif_stp_test",
    "otif_fill_test",
    "otif_count",
    "otif_ship_lines",
]

OUTPUT_FILE = INPUT_FILE.replace('.xlsx', '_otif_validation.xlsx')
# =========================================


def normalize_order_line(value):
    """Ensure order line is text with at least two decimals."""
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
    """Load and prepare data from Excel sheet"""
    df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)
    col_map = SAS_COLUMN_MAP if label == "SAS" else PBI_COLUMN_MAP
    
    # Check for missing columns
    missing = [col for col in col_map if col not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in {label} tab: {missing}")
    
    # Rename to standardized names
    rename_map = {orig: std for orig, std in col_map.items() if std != "Order.Line"}
    df = df.rename(columns=rename_map)
    
    # Normalize Order.Line
    if COLUMN_NAME not in df.columns:
        raise KeyError(f"Key column '{COLUMN_NAME}' missing after rename in {label} tab")
    df[COLUMN_NAME] = df[COLUMN_NAME].apply(normalize_order_line)
    
    print(f"{label} tab: {len(df):,} rows loaded")
    
    return df


def aggregate_by_order_line(df, metrics):
    """Aggregate metrics by Order.Line (sum all rows for each Order.Line)"""
    agg_dict = {metric: 'sum' for metric in metrics}
    aggregated = df.groupby(COLUMN_NAME).agg(agg_dict).reset_index()
    return aggregated


def find_order_line_differences(sas_agg, pbi_agg, metric):
    """
    Find Order.Lines where the aggregated metric value differs between SAS and PBI.
    Returns DataFrame with Order.Line and values from both systems.
    """
    # Merge aggregated data
    merged = pd.merge(
        sas_agg[[COLUMN_NAME, metric]],
        pbi_agg[[COLUMN_NAME, metric]],
        on=COLUMN_NAME,
        how='outer',
        suffixes=('_sas', '_pbi')
    )
    
    sas_col = f"{metric}_sas"
    pbi_col = f"{metric}_pbi"
    
    # Fill NaN with 0 for comparison (Order.Line exists in one system but not the other)
    merged[sas_col] = merged[sas_col].fillna(0)
    merged[pbi_col] = merged[pbi_col].fillna(0)
    
    # Find differences
    differences = merged[merged[sas_col] != merged[pbi_col]].copy()
    differences['Difference'] = differences[sas_col] - differences[pbi_col]
    
    # Rename columns for clarity
    differences = differences.rename(columns={
        sas_col: f'SAS_{metric}',
        pbi_col: f'PBI_{metric}'
    })
    
    return differences[[COLUMN_NAME, f'SAS_{metric}', f'PBI_{metric}', 'Difference']]


def main():
    print("=" * 70)
    print("OTIF Validation: SAS vs PBI")
    print("=" * 70)
    
    # Load data
    try:
        print("\nLoading data...")
        sas = load_and_prepare(SAS_TAB, "SAS")
        pbi = load_and_prepare(PBI_TAB, "PBI")
    except Exception as exc:
        print(f"Error loading data: {exc}")
        sys.exit(1)
    
    # Aggregate by Order.Line
    print("\nAggregating by Order.Line...")
    sas_agg = aggregate_by_order_line(sas, METRICS)
    pbi_agg = aggregate_by_order_line(pbi, METRICS)
    
    print(f"  SAS: {len(sas_agg):,} unique Order.Lines")
    print(f"  PBI: {len(pbi_agg):,} unique Order.Lines")
    
    # Compare aggregate sums for each metric
    print("\n" + "=" * 70)
    print("AGGREGATE COMPARISON")
    print("=" * 70)
    
    summary_data = []
    mismatched_metrics = []
    
    for metric in METRICS:
        sas_sum = sas_agg[metric].sum()
        pbi_sum = pbi_agg[metric].sum()
        difference = sas_sum - pbi_sum
        match = "✓" if difference == 0 else "✗"
        
        summary_data.append({
            'Metric': metric,
            'SAS_Total': sas_sum,
            'PBI_Total': pbi_sum,
            'Difference': difference,
            'Match': match
        })
        
        print(f"\n{metric}:")
        print(f"  SAS Total: {sas_sum:,.0f}")
        print(f"  PBI Total: {pbi_sum:,.0f}")
        print(f"  Difference: {difference:,.0f} {match}")
        
        if difference != 0:
            mismatched_metrics.append(metric)
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    # If all metrics match, we're done
    if not mismatched_metrics:
        print("\n" + "=" * 70)
        print("✓ ALL METRICS MATCH - No discrepancies found!")
        print("=" * 70)
        
        # Still write summary to Excel
        try:
            with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            print(f"\nSummary written to: {OUTPUT_FILE}")
        except Exception as exc:
            print(f"Error writing output: {exc}")
        
        return
    
    # Find Order.Line differences for mismatched metrics
    print("\n" + "=" * 70)
    print("ORDER.LINE LEVEL ANALYSIS")
    print("=" * 70)
    
    detail_sheets = {}
    
    for metric in mismatched_metrics:
        print(f"\nAnalyzing {metric}...")
        differences = find_order_line_differences(sas_agg, pbi_agg, metric)
        
        if not differences.empty:
            detail_sheets[metric] = differences
            print(f"  Found {len(differences):,} Order.Lines with differences")
            print(f"  Total discrepancy: {differences['Difference'].sum():,.0f}")
    
    # Write results to Excel
    print("\n" + "=" * 70)
    print("WRITING RESULTS")
    print("=" * 70)
    
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            # Summary sheet
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            print(f"✓ Summary sheet written")
            
            # Detail sheets for each mismatched metric
            for metric, df in detail_sheets.items():
                # Create clean sheet name (Excel has 31 char limit)
                sheet_name = metric.replace('_', ' ').title()[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"✓ {sheet_name} sheet written ({len(df):,} rows)")
        
        print(f"\n✓ Results written to: {OUTPUT_FILE}")
        print(f"  Total sheets: {1 + len(detail_sheets)}")
        
    except Exception as exc:
        print(f"✗ Error writing output: {exc}")
        sys.exit(1)
    
    # Final summary
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Metrics validated: {len(METRICS)}")
    print(f"Metrics matched: {len(METRICS) - len(mismatched_metrics)}")
    print(f"Metrics with discrepancies: {len(mismatched_metrics)}")
    if mismatched_metrics:
        print(f"  - {', '.join(mismatched_metrics)}")
    print("=" * 70)


if __name__ == '__main__':
    main()