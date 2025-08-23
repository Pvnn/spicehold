
from src.data_processing.data_cleaner import CardamomDataCleaner
from src.data_processing.feature_engineer import PriceFeatureEngineer

# File paths
raw_path = 'data/raw/cardamom_auction_data.csv'
processed_path = 'data/processed/clean_auction_data.csv'

# Step 1: Clean data
cleaner = CardamomDataCleaner(raw_path)
df_clean = cleaner.process_data()
cleaner.save_processed_data(processed_path)

# Step 2: Feature engineering
fe = PriceFeatureEngineer(df_clean)
df_features = fe.create_ml_features()

# Save feature engineered data
feature_engineered_path = 'data/processed/feature_engineered_data.csv'
df_features.to_csv(feature_engineered_path, index=False)

print('✅ Data cleaning & feature engineering complete!')
print(f'Saved cleaned data at: {processed_path}')
print(f'Saved feature engineered data at: {feature_engineered_path}')
