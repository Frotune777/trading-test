"""
Comprehensive data validation for all exported CSVs
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np


class DataValidator:
    """Validate all exported data for quality issues."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.stats = {}
        
    def validate_all_csvs(self, folder_path: str):
        """Validate all CSV files in a folder."""
        folder = Path(folder_path)
        
        print("="*80)
        print(f"🔍 VALIDATING DATA IN: {folder}")
        print("="*80)
        
        csv_files = list(folder.rglob('*.csv'))
        
        if not csv_files:
            print("❌ No CSV files found!")
            return
        
        print(f"\n📊 Found {len(csv_files)} CSV files\n")
        
        for csv_file in csv_files:
            print(f"\n📄 Validating: {csv_file.name}")
            print("-" * 60)
            
            try:
                df = pd.read_csv(csv_file)
                self._validate_file(csv_file.name, df)
            except Exception as e:
                self.issues.append(f"{csv_file.name}: Failed to read - {e}")
                print(f"   ❌ ERROR: {e}")
        
        self._print_summary()
    
    def _validate_file(self, filename: str, df: pd.DataFrame):
        """Validate a single CSV file."""
        
        # Check if empty
        if df.empty:
            self.issues.append(f"{filename}: Empty file")
            print("   ❌ Empty DataFrame")
            return
        
        print(f"   📊 Rows: {len(df)}, Columns: {len(df.columns)}")
        
        # Validate based on file type
        if 'price' in filename.lower():
            self._validate_price_data(filename, df)
        elif 'historical' in filename.lower() or 'intraday' in filename.lower():
            self._validate_ohlcv_data(filename, df)
        elif 'corporate' in filename.lower() or 'bulk' in filename.lower():
            self._validate_date_columns(filename, df)
        elif 'info' in filename.lower():
            self._validate_company_info(filename, df)
        
        # Generic validations
        self._check_missing_values(filename, df)
        
    def _validate_price_data(self, filename: str, df: pd.DataFrame):
        """Validate price data."""
        
        # Check for required columns
        price_cols = ['last_price', 'open', 'high', 'low', 'close']
        existing_cols = [col for col in price_cols if col in df.columns]
        
        if not existing_cols:
            self.warnings.append(f"{filename}: No price columns found")
            return
        
        for col in existing_cols:
            # Check for negative prices
            if (df[col] < 0).any():
                negative_count = (df[col] < 0).sum()
                self.issues.append(f"{filename}: {col} has {negative_count} negative values")
                print(f"   ❌ {col}: {negative_count} negative prices")
            
            # Check for zero prices
            if (df[col] == 0).any():
                zero_count = (df[col] == 0).sum()
                self.warnings.append(f"{filename}: {col} has {zero_count} zero values")
                print(f"   ⚠️  {col}: {zero_count} zero prices")
            
            # Check for unrealistic prices (> 1 crore)
            if (df[col] > 10000000).any():
                unrealistic_count = (df[col] > 10000000).sum()
                self.issues.append(f"{filename}: {col} has {unrealistic_count} unrealistic values")
                print(f"   ❌ {col}: {unrealistic_count} prices > 1 crore")
        
        # Validate High >= Low
        if 'high' in df.columns and 'low' in df.columns:
            invalid = df['high'] < df['low']
            if invalid.any():
                invalid_count = invalid.sum()
                self.issues.append(f"{filename}: {invalid_count} rows where High < Low")
                print(f"   ❌ {invalid_count} rows: High < Low")
        
        print("   ✅ Price validation complete")
    
    def _validate_ohlcv_data(self, filename: str, df: pd.DataFrame):
        """Validate OHLCV (candlestick) data."""
        
        # Check for OHLCV columns
        required_cols = ['Open', 'High', 'Low', 'Close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.issues.append(f"{filename}: Missing columns {missing_cols}")
            print(f"   ❌ Missing: {', '.join(missing_cols)}")
            return
        
        # Validate relationships
        issues_found = []
        
        # High should be >= Open, Close, Low
        if not (df['High'] >= df['Open']).all():
            issues_found.append("High < Open")
        if not (df['High'] >= df['Close']).all():
            issues_found.append("High < Close")
        if not (df['High'] >= df['Low']).all():
            issues_found.append("High < Low")
        
        # Low should be <= Open, Close, High
        if not (df['Low'] <= df['Open']).all():
            issues_found.append("Low > Open")
        if not (df['Low'] <= df['Close']).all():
            issues_found.append("Low > Close")
        
        if issues_found:
            self.issues.append(f"{filename}: OHLC relationship errors - {', '.join(issues_found)}")
            print(f"   ❌ OHLC issues: {', '.join(issues_found)}")
        
        # Check for negative volume
        if 'Volume' in df.columns:
            if (df['Volume'] < 0).any():
                negative_vol = (df['Volume'] < 0).sum()
                self.issues.append(f"{filename}: {negative_vol} negative volumes")
                print(f"   ❌ {negative_vol} negative volumes")
        
        # Validate dates/timestamps
        self._validate_timestamps(filename, df)
        
        if not issues_found:
            print("   ✅ OHLCV validation passed")
    
    def _validate_timestamps(self, filename: str, df: pd.DataFrame):
        """Validate date/timestamp columns."""
        
        date_columns = []
        
        # Check index
        if df.index.name in ['Timestamp', 'Date', 'date', 'timestamp']:
            date_columns.append(df.index.name)
        
        # Check columns
        for col in df.columns:
            if 'date' in col.lower() or 'timestamp' in col.lower():
                date_columns.append(col)
        
        if not date_columns:
            return
        
        for col in date_columns:
            try:
                # Get the date column
                if col == df.index.name:
                    dates = pd.to_datetime(df.index)
                else:
                    dates = pd.to_datetime(df[col])
                
                # Check for future dates (more than 1 day in future)
                future_threshold = datetime.now() + timedelta(days=1)
                future_dates = dates > future_threshold
                
                if future_dates.any():
                    future_count = future_dates.sum()
                    first_future = dates[future_dates].iloc[0]
                    self.issues.append(f"{filename}: {future_count} future dates (e.g., {first_future})")
                    print(f"   ❌ {future_count} future dates (first: {first_future})")
                
                # Check for very old dates (before 1990)
                old_threshold = pd.Timestamp('1990-01-01')
                old_dates = dates < old_threshold
                
                if old_dates.any():
                    old_count = old_dates.sum()
                    self.warnings.append(f"{filename}: {old_count} dates before 1990")
                    print(f"   ⚠️  {old_count} dates before 1990")
                
                # Check for sequential gaps in historical/intraday data
                if 'historical' in filename.lower() or 'intraday' in filename.lower():
                    self._check_date_gaps(filename, dates)
                
            except Exception as e:
                self.warnings.append(f"{filename}: Could not parse {col} as dates - {e}")
    
    def _check_date_gaps(self, filename: str, dates: pd.DatetimeIndex):
        """Check for unusual gaps in date sequence."""
        if len(dates) < 2:
            return
        
        dates_sorted = dates.sort_values()
        gaps = dates_sorted.diff()
        
        # For daily data, gap > 7 days is suspicious
        if 'daily' in filename.lower():
            large_gaps = gaps > timedelta(days=7)
            if large_gaps.any():
                gap_count = large_gaps.sum()
                max_gap = gaps.max()
                self.warnings.append(f"{filename}: {gap_count} large gaps (max: {max_gap})")
                print(f"   ⚠️  {gap_count} gaps > 7 days (max: {max_gap})")
        
        # For intraday, gap > 1 day is suspicious
        elif 'intraday' in filename.lower():
            large_gaps = gaps > timedelta(days=1)
            if large_gaps.any():
                gap_count = large_gaps.sum()
                self.warnings.append(f"{filename}: {gap_count} multi-day gaps in intraday data")
                print(f"   ⚠️  {gap_count} multi-day gaps")
    
    def _validate_date_columns(self, filename: str, df: pd.DataFrame):
        """Validate files with date columns (corporate actions, bulk deals)."""
        
        # Find date columns
        date_cols = [col for col in df.columns if 'date' in col.lower()]
        
        for col in date_cols:
            try:
                # Parse dates
                dates = pd.to_datetime(df[col], errors='coerce')
                
                # Check for unparseable dates
                invalid_dates = dates.isna() & df[col].notna()
                if invalid_dates.any():
                    invalid_count = invalid_dates.sum()
                    sample = df.loc[invalid_dates, col].iloc[0] if invalid_count > 0 else None
                    self.issues.append(f"{filename}: {col} has {invalid_count} unparseable dates (e.g., '{sample}')")
                    print(f"   ❌ {col}: {invalid_count} unparseable dates")
                
                # Check for future dates
                valid_dates = dates[dates.notna()]
                if not valid_dates.empty:
                    future_threshold = datetime.now() + timedelta(days=1)
                    future_dates = valid_dates > future_threshold
                    
                    if future_dates.any():
                        future_count = future_dates.sum()
                        first_future = valid_dates[future_dates].iloc[0]
                        self.issues.append(f"{filename}: {col} has {future_count} future dates (e.g., {first_future})")
                        print(f"   ❌ {col}: {future_count} future dates (first: {first_future})")
                        
                        # Show sample of problematic rows
                        print(f"   📋 Sample problematic dates:")
                        problem_rows = df[dates > future_threshold].head(3)
                        print(problem_rows[[col] + [c for c in ['symbol', 'subject'] if c in df.columns]].to_string(index=False))
                
            except Exception as e:
                self.warnings.append(f"{filename}: Error parsing {col} - {e}")
    
    def _validate_company_info(self, filename: str, df: pd.DataFrame):
        """Validate company information."""
        
        # Check for essential fields
        essential_fields = ['symbol', 'company_name']
        missing = [field for field in essential_fields if field not in df.columns]
        
        if missing:
            self.issues.append(f"{filename}: Missing essential fields {missing}")
            print(f"   ❌ Missing: {', '.join(missing)}")
        
        # Check if company name is filled
        if 'company_name' in df.columns:
            empty_names = df['company_name'].isna() | (df['company_name'] == '')
            if empty_names.any():
                self.issues.append(f"{filename}: {empty_names.sum()} rows with empty company name")
                print(f"   ❌ {empty_names.sum()} empty company names")
        
        print("   ✅ Company info validated")
    
    def _check_missing_values(self, filename: str, df: pd.DataFrame):
        """Check for missing values."""
        
        missing_summary = df.isna().sum()
        missing_pct = (missing_summary / len(df) * 100).round(1)
        
        high_missing = missing_pct[missing_pct > 50]
        
        if not high_missing.empty:
            for col, pct in high_missing.items():
                self.warnings.append(f"{filename}: {col} is {pct}% missing")
                print(f"   ⚠️  {col}: {pct}% missing values")
    
    def _print_summary(self):
        """Print validation summary."""
        
        print("\n" + "="*80)
        print("📊 VALIDATION SUMMARY")
        print("="*80)
        
        print(f"\n❌ Critical Issues: {len(self.issues)}")
        if self.issues:
            for issue in self.issues[:10]:  # Show first 10
                print(f"   • {issue}")
            if len(self.issues) > 10:
                print(f"   ... and {len(self.issues) - 10} more")
        
        print(f"\n⚠️  Warnings: {len(self.warnings)}")
        if self.warnings:
            for warning in self.warnings[:10]:
                print(f"   • {warning}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more")
        
        if not self.issues and not self.warnings:
            print("\n✅ All data looks good!")
        
        print("\n" + "="*80)


def main():
    """Run validation on a folder."""
    import sys
    
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = 'quick_verify/TCS'
    
    validator = DataValidator()
    validator.validate_all_csvs(folder)


if __name__ == '__main__':
    main()