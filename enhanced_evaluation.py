from src.models.price_forecaster import CardamomPriceForecaster
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import pandas as pd
import numpy as np

def comprehensive_evaluation():
    # Load your best tuned model
    forecaster = CardamomPriceForecaster('data/processed/clean_auction_data.csv')
    forecaster.load_model('data/models/tuned_cardamom_model.pkl')
    
    # Load test data
    data = forecaster.load_and_prepare_data()
    _, test_data = forecaster.split_data(data)
    
    # Generate predictions
    predictions = forecaster.model.predict(test_data[['ds']])
    
    y_true = test_data['y'].values
    y_pred = predictions['yhat'].values
    
    # Calculate comprehensive metrics
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)
    
    # Classification evaluation (HOLD vs SELL)
    recommendations = []
    actual_outcomes = []
    
    for i in range(len(test_data) - 7):  # 7-day horizon
        current_price = y_true[i]
        future_price = y_true[i + 7]
        
        # Get model recommendation
        rec = forecaster.get_sell_recommendation(
            current_price=current_price,
            days_ahead=7,
            start_date=test_data.iloc[i]['ds']
        )
        
        recommendations.append(1 if rec['action'] == 'HOLD' else 0)
        actual_outcomes.append(1 if future_price > current_price + 50 else 0)
    
    # Classification accuracy
    rec_accuracy = np.mean(np.array(recommendations) == np.array(actual_outcomes))
    
    # Save evaluation results
    results = {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'r2': r2,
        'recommendation_accuracy': rec_accuracy,
        'samples_tested': len(y_true),
        'timestamp': pd.Timestamp.now()
    }
    
    print("📊 FINAL MODEL EVALUATION:")
    print(f"   MAE: ₹{mae:.2f}/kg")
    print(f"   RMSE: ₹{rmse:.2f}/kg") 
    print(f"   MAPE: {mape:.2f}%")
    print(f"   R²: {r2:.3f}")
    print(f"   Recommendation Accuracy: {rec_accuracy:.1%}")
    
    # Save to file
    pd.DataFrame([results]).to_csv('model_evaluation_results.csv', index=False)
    return results

# Run evaluation
results = comprehensive_evaluation()
