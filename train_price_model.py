from src.models.price_forecaster import CardamomPriceForecaster
import os

def main():
    # Initialize forecaster
    forecaster = CardamomPriceForecaster('data/processed/clean_auction_data.csv')
    
    # Train model
    model = forecaster.train_model()
    
    # Generate 30-day forecast
    forecast = forecaster.forecast_prices(days_ahead=30)
    print("\n🔮 30-Day Price Forecast (First 10 days):")
    print(forecast.head(10).to_string(index=False))
    
    # Get AI recommendation
    recommendation = forecaster.get_sell_recommendation()
    
    print(f"\n🎯 SPICEHOLD AI RECOMMENDATION:")
    print(f"   Action: {recommendation['action']}")
    print(f"   Reason: {recommendation['reason']}")
    print(f"   Current Price: ₹{recommendation['current_price_estimate']:.0f}/kg")
    print(f"   Optimal Price: ₹{recommendation['optimal_price_estimate']:.0f}/kg")
    print(f"   Days to Wait: {recommendation['days_to_wait']} days")
    print(f"   Optimal Date: {recommendation['optimal_sell_date']}")
    
    os.makedirs('data/models', exist_ok=True)
    
    # Save model (now will work)
    forecaster.save_model('data/models/cardamom_price_model.pkl')
    
    print(f"\n✅ SpiceHold Price Forecasting Model Ready!")
    
    print(f"\n✅ SpiceHold Price Forecasting Model Ready!")

if __name__ == "__main__":
    main()
