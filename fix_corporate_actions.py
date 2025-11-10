"""
Fix corporate actions CSV by handling NSE's date format issues
"""

import pandas as pd
from pathlib import Path
import sys


def fix_corporate_actions(csv_path: str):
    """
    Fix corporate actions CSV:
    - Replace "-" with NaN in date columns
    - Try to parse dates correctly
    - Handle NSE's inconsistent date formats
    """
    
    print(f"🔧 Fixing: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    print(f"   📊 Original: {len(df)} rows, {len(df.columns)} columns")
    
    # Find date columns
    date_columns = [col for col in df.columns if 'date' in col.lower()]
    
    print(f"   📅 Date columns: {', '.join(date_columns)}")
    
    # Replace "-" with NaN
    for col in date_columns:
        # Replace various forms of "missing" with NaN
        df[col] = df[col].replace(['-', '', 'None', 'N/A', 'NA'], pd.NA)
        
        # Try to parse as datetime
        df[col] = pd.to_datetime(df[col], format='%d-%b-%Y', errors='coerce')
    
    # Count improvements
    issues_before = sum((df[col] == '-').sum() for col in date_columns if col in df.columns)
    issues_after = sum(df[col].isna().sum() for col in date_columns if col in df.columns)
    
    print(f"   ✅ Fixed: {issues_before} '-' values → {issues_after} NaN values")
    
    # Save cleaned version
    output_path = Path(csv_path).parent / (Path(csv_path).stem + '_cleaned.csv')
    df.to_csv(output_path, index=False)
    
    print(f"   💾 Saved: {output_path}")
    
    # Also update original
    df.to_csv(csv_path, index=False)
    print(f"   💾 Updated: {csv_path}")
    
    return df


def main():
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = 'quick_verify/TCS/TCS_corporate_actions.csv'
    
    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        return
    
    df = fix_corporate_actions(csv_path)
    
    # Show sample
    print("\n📋 Sample cleaned data:")
    print(df[['symbol', 'subject', 'exDate', 'recDate']].head().to_string(index=False))
    
    print("\n✅ Done! Date columns now properly formatted.")


if __name__ == '__main__':
    main()