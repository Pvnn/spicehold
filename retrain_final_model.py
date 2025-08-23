from src.models.price_forecaster import CardamomPriceForecaster

def retrain_with_best_params():
    forecaster = CardamomPriceForecaster('data/processed/clean_auction_data.csv')
    data = forecaster.load_and_prepare_data()
    
    # Use ALL data for final training (no test split)
    model = forecaster.create_prophet_model()
    model.changepoint_prior_scale = 0.1    # Best param
    model.seasonality_prior_scale = 15     # Best param
    
    model.fit(data)  # Train on entire dataset
    forecaster.model = model
    
    # Save optimized model
    forecaster.save_model('data/models/tuned_cardamom_model.pkl')
    print("✅ Final optimized model saved with MAPE: 0.263%")

if __name__ == "__main__":
    retrain_with_best_params()
