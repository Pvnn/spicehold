import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CardamomEDA:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
    
    def load_data(self):
        """Load processed cardamom data"""
        self.df = pd.read_csv(self.data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        print(f"📊 Loaded {len(self.df)} cardamom auction records")
        return self.df
    
    def basic_stats(self):
        """Display basic dataset statistics"""
        print("=" * 50)
        print("📈 CARDAMOM AUCTION DATA OVERVIEW")
        print("=" * 50)
        
        print(f"📅 Date Range: {self.df['date'].min()} to {self.df['date'].max()}")
        print(f"📊 Total Records: {len(self.df):,}")
        print(f"🏢 Unique Auctioneers: {self.df['auctioneer'].nunique()}")
        
        print("\n💰 PRICE STATISTICS (Rs/kg):")
        price_stats = self.df['avg_price_rs_kg'].describe()
        print(f"   Average Price: ₹{price_stats['mean']:.2f}")
        print(f"   Median Price: ₹{price_stats['50%']:.2f}")
        print(f"   Min Price: ₹{price_stats['min']:.2f}")
        print(f"   Max Price: ₹{price_stats['max']:.2f}")
        print(f"   Price Volatility (Std): ₹{price_stats['std']:.2f}")
        
        print("\n📦 VOLUME STATISTICS (kg):")
        volume_stats = self.df['total_arrival_kg'].describe()
        print(f"   Average Daily Volume: {volume_stats['mean']:,.0f} kg")
        print(f"   Median Daily Volume: {volume_stats['50%']:,.0f} kg")
        print(f"   Max Daily Volume: {volume_stats['max']:,.0f} kg")
        
        print("\n🎯 MARKET EFFICIENCY:")
        avg_efficiency = self.df['market_efficiency'].mean() * 100
        print(f"   Average Sell-through Rate: {avg_efficiency:.1f}%")
        
    def price_trends_analysis(self):
      """Analyze price trends with proper volatility calculation"""
      print("\n" + "=" * 50)
      print("📈 PRICE TREND ANALYSIS")
      print("=" * 50)
      
      # Clean price data before volatility calculation
      clean_prices = self.df['avg_price_rs_kg'].dropna()
      
      if len(clean_prices) > 1:
          # Calculate price change on clean data
          price_change = clean_prices.pct_change() * 100
          avg_volatility = price_change.std()
          print(f"\n📊 Average Daily Price Volatility: {avg_volatility:.2f}%")
      else:
          print(f"\n📊 Average Daily Price Volatility: Insufficient data")

    def seasonal_patterns(self):
        """Identify seasonal patterns in cardamom prices"""
        print("\n" + "=" * 50)
        print("🌍 SEASONAL PATTERN ANALYSIS")
        print("=" * 50)
        
        # Add time features
        self.df['day_of_week'] = self.df['date'].dt.day_name()
        self.df['month_name'] = self.df['date'].dt.month_name()
        self.df['quarter'] = self.df['date'].dt.quarter
        
        # Weekly patterns
        weekly_prices = self.df.groupby('day_of_week')['avg_price_rs_kg'].mean().sort_values(ascending=False)
        print("\n📅 AVERAGE PRICES BY DAY OF WEEK:")
        for day, price in weekly_prices.items():
            print(f"   {day}: ₹{price:.2f}")
        
        # Monthly patterns
        monthly_prices = self.df.groupby('month_name')['avg_price_rs_kg'].mean()
        print(f"\n🗓️  HIGHEST PRICE MONTHS:")
        top_months = monthly_prices.sort_values(ascending=False).head(3)
        for month, price in top_months.items():
            print(f"   {month}: ₹{price:.2f}")
        
        # Quarterly patterns
        quarterly_prices = self.df.groupby('quarter')['avg_price_rs_kg'].mean()
        print(f"\n📊 QUARTERLY PRICE AVERAGES:")
        for quarter, price in quarterly_prices.items():
            seasons = {1: "Jan-Mar", 2: "Apr-Jun", 3: "Jul-Sep", 4: "Oct-Dec"}
            print(f"   Q{quarter} ({seasons[quarter]}): ₹{price:.2f}")
    
    def volume_price_relationship(self):
        """Analyze relationship between volume and prices"""
        print("\n" + "=" * 50)
        print("📊 VOLUME-PRICE RELATIONSHIP")
        print("=" * 50)
        
        # Correlation analysis
        correlation = self.df['total_arrival_kg'].corr(self.df['avg_price_rs_kg'])
        print(f"\n📈 Volume-Price Correlation: {correlation:.3f}")
        
        if correlation < -0.3:
            print("   ⬇️  Strong inverse relationship: Higher volume → Lower prices")
        elif correlation > 0.3:
            print("   ⬆️  Strong positive relationship: Higher volume → Higher prices")
        else:
            print("   ➡️  Weak relationship between volume and prices")
        
        # Volume categories analysis
        self.df['volume_category'] = pd.cut(self.df['total_arrival_kg'], 
                                          bins=3, 
                                          labels=['Low Volume', 'Medium Volume', 'High Volume'])
        
        volume_price_analysis = self.df.groupby('volume_category')['avg_price_rs_kg'].agg(['mean', 'std'])
        print(f"\n📦 PRICE BY VOLUME CATEGORY:")
        for category, data in volume_price_analysis.iterrows():
            print(f"   {category}: ₹{data['mean']:.2f} (±₹{data['std']:.2f})")
    
    def top_performers_analysis(self):
        """Analyze top performing auctioneers"""
        print("\n" + "=" * 50)
        print("🏆 TOP PERFORMING AUCTIONEERS")
        print("=" * 50)
        
        # Top auctioneers by average price
        auctioneer_stats = self.df.groupby('auctioneer').agg({
            'avg_price_rs_kg': ['mean', 'count'],
            'total_arrival_kg': 'sum'
        }).round(2)
        
        # Flatten column names
        auctioneer_stats.columns = ['avg_price', 'auction_count', 'total_volume']
        
        # Filter auctioneers with at least 10 auctions
        significant_auctioneers = auctioneer_stats[auctioneer_stats['auction_count'] >= 10]
        top_by_price = significant_auctioneers.sort_values('avg_price', ascending=False).head(5)
        
        print("\n💰 TOP 5 AUCTIONEERS BY AVERAGE PRICE:")
        for auctioneer, data in top_by_price.iterrows():
            short_name = auctioneer.split(',')[0][:30]  # Truncate long names
            print(f"   {short_name}: ₹{data['avg_price']:.2f} ({data['auction_count']} auctions)")
    
    def data_quality_check(self):
        """Check data quality and completeness"""
        print("\n" + "=" * 50)
        print("🔍 DATA QUALITY ASSESSMENT")
        print("=" * 50)
        
        # Missing values
        missing_data = self.df.isnull().sum()
        total_missing = missing_data.sum()
        
        if total_missing == 0:
            print("✅ No missing values found!")
        else:
            print("⚠️  Missing values detected:")
            for col, missing in missing_data[missing_data > 0].items():
                print(f"   {col}: {missing} missing values")
        
        # Outliers detection
        price_q1 = self.df['avg_price_rs_kg'].quantile(0.25)
        price_q3 = self.df['avg_price_rs_kg'].quantile(0.75)
        price_iqr = price_q3 - price_q1
        price_outliers = len(self.df[
            (self.df['avg_price_rs_kg'] < price_q1 - 1.5 * price_iqr) |
            (self.df['avg_price_rs_kg'] > price_q3 + 1.5 * price_iqr)
        ])
        
        print(f"\n📊 Price Outliers Detected: {price_outliers} records ({price_outliers/len(self.df)*100:.2f}%)")
        
        # Data completeness
        data_completeness = (1 - total_missing / (len(self.df) * len(self.df.columns))) * 100
        print(f"📈 Overall Data Completeness: {data_completeness:.1f}%")
    
    def generate_insights(self):
        """Generate key business insights"""
        print("\n" + "=" * 60)
        print("💡 KEY BUSINESS INSIGHTS FOR SPICEHOLD")
        print("=" * 60)
        
        # Price volatility insights
        daily_volatility = self.df['avg_price_rs_kg'].std()
        avg_price = self.df['avg_price_rs_kg'].mean()
        volatility_percent = (daily_volatility / avg_price) * 100
        
        print(f"🎯 FARMER OPPORTUNITY:")
        print(f"   Price volatility: {volatility_percent:.1f}% of average price")
        print(f"   This means farmers can gain/lose ₹{daily_volatility:.2f}/kg by timing sales")
        
        # Best selling windows
        self.df['month'] = self.df['date'].dt.month
        best_months = self.df.groupby('month')['avg_price_rs_kg'].mean().sort_values(ascending=False).head(3)
        worst_months = self.df.groupby('month')['avg_price_rs_kg'].mean().sort_values(ascending=True).head(3)
        
        month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun',
                      7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
        
        print(f"\n📅 OPTIMAL SELLING PERIODS:")
        for month, price in best_months.items():
            print(f"   {month_names[month]}: ₹{price:.2f} (Best months to sell)")
        
        print(f"\n❌ AVOID SELLING IN:")
        for month, price in worst_months.items():
            print(f"   {month_names[month]}: ₹{price:.2f} (Lowest price months)")
        
        # Market efficiency insight
        avg_unsold = self.df['unsold_percentage'].mean() * 100
        print(f"\n📊 MARKET DEMAND:")
        print(f"   Average unsold inventory: {avg_unsold:.1f}%")
        print(f"   Market demand is {'STRONG' if avg_unsold < 10 else 'MODERATE' if avg_unsold < 20 else 'WEAK'}")
    
    def run_full_eda(self):
        """Run complete EDA analysis"""
        self.load_data()
        self.basic_stats()
        self.price_trends_analysis()
        self.seasonal_patterns()
        self.volume_price_relationship()
        self.top_performers_analysis()
        self.data_quality_check()
        self.generate_insights()
        
        print(f"\n✅ EDA COMPLETE - Ready for model building!")

# Usage
if __name__ == "__main__":
    eda = CardamomEDA('data/processed/clean_auction_data.csv')
    eda.run_full_eda()
