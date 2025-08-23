import pandas as pd
import numpy as np

class CardamomDataCleaner:
    def __init__(self, raw_data_path):
        self.raw_data_path = raw_data_path
        self.processed_data = None
    
    def load_raw_data(self):
        """Load raw auction data from CSV with header cleaning and numeric conversion"""
        try:
            df = pd.read_csv(self.raw_data_path)
            df.columns = df.columns.str.strip()
            
            # Convert numeric columns
            numeric_cols = [
                'Total Qty Arrived (Kgs)',
                'Qty Sold (Kgs)',
                'MaxPrice (Rs./Kg)',
                'Avg.Price (Rs./Kg)',
                'No.of Lots'
            ]
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            print(f"✅ Loaded {len(df)} records from {self.raw_data_path}")
            print(f"📋 Column names found: {list(df.columns)}")
            return df
        except FileNotFoundError:
            print(f"❌ File not found: {self.raw_data_path}")
            return None
    
    def clean_dates(self, df):
        """Convert date column to proper datetime format"""
        date_col = 'Date of Auction'
        if date_col in df.columns:
            df['date'] = pd.to_datetime(df[date_col], format='%d-%m-%Y', errors='coerce')
            df = df.drop(date_col, axis=1)
        return df
    
    def standardize_columns(self, df):
        """Rename columns to follow consistent naming convention"""
        column_mapping = {}
        
        for col in df.columns:
            if 'Auctioneer' in col:
                column_mapping[col] = 'auctioneer'
            elif 'No.of Lots' in col or 'Lots' in col:
                column_mapping[col] = 'num_lots'
            elif 'Total Qty' in col and 'Arrived' in col:
                column_mapping[col] = 'total_arrival_kg'
            elif 'Qty Sold' in col:
                column_mapping[col] = 'qty_sold_kg'
            elif 'MaxPrice' in col or 'Max Price' in col:
                column_mapping[col] = 'max_price_rs_kg'
            elif 'Avg.Price' in col or 'Avg Price' in col:
                column_mapping[col] = 'avg_price_rs_kg'
        
        print(f"🏷️  Column mappings: {column_mapping}")
        df = df.rename(columns=column_mapping)
        return df
    
    def clean_and_validate_data(self, df):
        """Enhanced data cleaning with quality validation"""
        print("🧹 Performing enhanced data cleaning...")
        
        # 1. Handle zero prices (replace with NaN)
        price_columns = ['avg_price_rs_kg', 'max_price_rs_kg']
        for col in price_columns:
            if col in df.columns:
                zero_count = (df[col] == 0).sum()
                if zero_count > 0:
                    print(f"   ⚠️  Found {zero_count} zero values in {col} - replacing with NaN")
                    df[col] = df[col].replace(0, np.nan)
        
        # 2. Remove unrealistic price outliers (>₹5000 or negative)
        for col in price_columns:
            if col in df.columns:
                outlier_high = (df[col] > 5000).sum()
                if outlier_high > 0:
                    print(f"   🔥 Removing {outlier_high} unrealistic high prices (>₹5000) from {col}")
                    df.loc[df[col] > 5000, col] = np.nan
        
        # 3. Handle volume data quality
        volume_columns = ['total_arrival_kg', 'qty_sold_kg']
        for col in volume_columns:
            if col in df.columns:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    print(f"   📦 Removing {negative_count} negative volumes from {col}")
                    df.loc[df[col] < 0, col] = np.nan
        
        # 4. Interpolate missing prices (use ffill/bfill instead of deprecated method)
        for col in price_columns:
            if col in df.columns:
                before_missing = df[col].isna().sum()
                df[col] = df[col].ffill().bfill()  # Updated method
                after_missing = df[col].isna().sum()
                if before_missing > after_missing:
                    print(f"   💉 Imputed {before_missing - after_missing} missing values in {col}")
        
        # 5. Remove rows where both price and volume are completely missing
        critical_columns = ['avg_price_rs_kg', 'total_arrival_kg']
        rows_before = len(df)
        df = df.dropna(subset=critical_columns, how='all')
        rows_after = len(df)
        
        if rows_before - rows_after > 0:
            print(f"   🗑️  Removed {rows_before - rows_after} rows with no useful data")
        
        return df
    
    def calculate_market_metrics(self, df):
        """Add calculated columns for market analysis - USES STANDARDIZED COLUMN NAMES"""
        
        # Apply data cleaning first
        df = self.clean_and_validate_data(df)
        
        # Calculate metrics using standardized column names
        df['unsold_qty_kg'] = df['total_arrival_kg'] - df['qty_sold_kg']
        df['unsold_percentage'] = df['unsold_qty_kg'] / df['total_arrival_kg']
        df['price_spread'] = df['max_price_rs_kg'] - df['avg_price_rs_kg']
        df['market_efficiency'] = df['qty_sold_kg'] / df['total_arrival_kg']
        
        return df
    
    def process_data(self):
        """Main processing pipeline"""
        print("🔄 Starting data processing...")
        
        # Load raw data
        df = self.load_raw_data()
        if df is None:
            return None
        
        # Apply cleaning steps IN CORRECT ORDER
        df = self.clean_dates(df)
        df = self.standardize_columns(df)      # ✅ Rename columns FIRST
        df = self.calculate_market_metrics(df) # ✅ Then use renamed columns
        
        # Sort by date and remove invalid dates
        df = df.dropna(subset=['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        self.processed_data = df
        print(f"✅ Data processing complete. {len(df)} records processed.")
        
        return df
    
    def save_processed_data(self, output_path):
        """Save cleaned data to CSV"""
        if self.processed_data is not None:
            self.processed_data.to_csv(output_path, index=False)
            print(f"💾 Processed data saved to: {output_path}")
        else:
            print("❌ No processed data to save. Run process_data() first.")
