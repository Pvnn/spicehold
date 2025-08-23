import pandas as pd
import numpy as np

class PriceFeatureEngineer:
    def __init__(self, processed_data):
        self.data = processed_data
    
    def add_time_features(self, df):
        """Add time-based features for forecasting"""
        df['day_of_week'] = df['date'].dt.day_name()
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        
        return df
    
    def add_price_trends(self, df):
        """Calculate price movement indicators"""
        # Sort by date for trend calculation
        df = df.sort_values('date')
        
        # Rolling averages (3-day window)
        df['price_ma_3d'] = df['avg_price_rs_kg'].rolling(window=3, min_periods=1).mean()
        
        # Price change from previous day
        df['price_change'] = df['avg_price_rs_kg'].diff()
        df['price_change_pct'] = df['avg_price_rs_kg'].pct_change() * 100
        
        # Volatility (rolling standard deviation)
        df['price_volatility'] = df['avg_price_rs_kg'].rolling(window=3, min_periods=1).std()
        
        return df
    
    def add_volume_features(self, df):
        """Add volume-based market indicators"""
        # Volume trends
        df['volume_ma_3d'] = df['total_arrival_kg'].rolling(window=3, min_periods=1).mean()
        df['volume_change_pct'] = df['total_arrival_kg'].pct_change() * 100
        
        # Price-volume relationship
        df['price_volume_ratio'] = df['avg_price_rs_kg'] / (df['total_arrival_kg'] / 1000)
        
        return df
    
    def create_ml_features(self):
        """Generate all features for machine learning"""
        df = self.data.copy()
        
        # Add all feature categories
        df = self.add_time_features(df)
        df = self.add_price_trends(df)
        df = self.add_volume_features(df)
        
        # Fill NaN values (from diff/pct_change operations)
        df = df.fillna(method='bfill').fillna(method='ffill')
        
        return df
