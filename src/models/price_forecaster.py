import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

class CardamomPriceForecaster:
    def __init__(self, processed_data_path):
        self.data_path = processed_data_path
        self.model = None
        self.forecast = None
        self.train_data = None
        self.test_data = None
        self.metrics = {}
    
    def load_and_prepare_data(self):
        """Load processed data and prepare for Prophet"""
        print("📊 Loading processed cardamom data...")
        df = pd.read_csv(self.data_path)
        
        # Prepare for Prophet (requires 'ds' and 'y' columns)
        prophet_data = df[['date', 'avg_price_rs_kg']].copy()
        prophet_data.columns = ['ds', 'y']
        prophet_data['ds'] = pd.to_datetime(prophet_data['ds'])
        
        # Remove missing values
        prophet_data = prophet_data.dropna()
        
        print(f"✅ Prepared {len(prophet_data)} records for forecasting")
        print(f"📅 Date range: {prophet_data['ds'].min()} to {prophet_data['ds'].max()}")
        print(f"💰 Price range: ₹{prophet_data['y'].min():.0f} - ₹{prophet_data['y'].max():.0f} per kg")
        
        return prophet_data
    
    def split_data(self, data, test_size=0.2):
        """Split data chronologically into train/test sets"""
        split_idx = int(len(data) * (1 - test_size))
        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]
        
        print(f"🔄 Data split: {len(train_data)} training, {len(test_data)} testing records")
        print(f"📅 Training period: {train_data['ds'].min()} to {train_data['ds'].max()}")
        print(f"📅 Testing period: {test_data['ds'].min()} to {test_data['ds'].max()}")
        
        self.train_data = train_data
        self.test_data = test_data
        
        return train_data, test_data
    
    def create_prophet_model(self, tuned_params=None):
      """Create optimized Prophet model"""
      if tuned_params is None:
          # Your current defaults
          params = {
              'changepoint_prior_scale': 0.05,
              'seasonality_prior_scale': 10.0
          }
      else:
          params = tuned_params
      
      model = Prophet(
          yearly_seasonality=True,
          weekly_seasonality=True,
          daily_seasonality=False,
          changepoint_prior_scale=params['changepoint_prior_scale'],
          seasonality_prior_scale=params['seasonality_prior_scale'],
          interval_width=0.80,
          seasonality_mode='additive'
      )
      
      # Add quarterly seasonality
      model.add_seasonality(name='quarterly', period=365.25/4, fourier_order=4)
      
      self.model = model
      return model

    
    def train_model(self):
        """Train Prophet model on cardamom auction data"""
        print("🎯 Training Prophet model for cardamom price forecasting...")
        
        # Load and prepare data
        data = self.load_and_prepare_data()
        train_data, test_data = self.split_data(data)
        
        # Create and train model
        model = self.create_prophet_model()
        model.fit(train_data)
        
        print("✅ Model training complete!")
        
        # Validate performance
        self.validate_model(test_data)
        
        return model
    
    def validate_model(self, test_data):
        """Validate model performance on holdout test data"""
        print("📈 Validating model performance...")
        
        # Make predictions on test set
        test_forecast = self.model.predict(test_data[['ds']])
        
        # Calculate performance metrics
        y_true = test_data['y'].values
        y_pred = test_forecast['yhat'].values
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        r2 = r2_score(y_true, y_pred)
        
        # Store metrics
        self.metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
        print(f"   R²: {r2:.3f}")
        print(f"📊 Model Performance Metrics:")
        print(f"   MAE (Mean Absolute Error): ₹{mae:.2f}/kg")
        print(f"   RMSE (Root Mean Square Error): ₹{rmse:.2f}/kg")
        print(f"   MAPE (Mean Absolute % Error): {mape:.2f}%")
        
        # Performance interpretation
        avg_price = y_true.mean()
        mae_percent = (mae / avg_price) * 100
        
        if mae_percent < 5:
            print("   🎯 Excellent prediction accuracy!")
        elif mae_percent < 10:
            print("   ✅ Good prediction accuracy")
        else:
            print("   ⚠️  Moderate prediction accuracy - consider model tuning")
        results_df = pd.DataFrame({
            'date': test_data['ds'],
            'actual_price': y_true,
            'predicted_price': y_pred
        })
        results_df.to_csv('cardamom_test_predictions.csv', index=False)
        
        return self.metrics
    
    def forecast_prices(self, days_ahead=30, start_date=None):
      """Generate future price forecasts starting from a specific date"""
      print(f"🔮 Generating {days_ahead}-day price forecast...")
      
      # Use today's date if no start date provided
      if start_date is None:
          start_date = pd.to_datetime(datetime.now().date())
      else:
          start_date = pd.to_datetime(start_date)
      print(f"🗓️ DEBUG: Forecasting from {start_date.strftime('%Y-%m-%d')}")
      
      # Create future dataframe starting from specified date
      future_dates = pd.date_range(start=start_date, periods=days_ahead, freq='D')
      future = pd.DataFrame({'ds': future_dates})

      print(f"🗓️ DEBUG: First forecast date: {future_dates[0].strftime('%Y-%m-%d')}")
      print(f"🗓️ DEBUG: Last forecast date: {future_dates[-1].strftime('%Y-%m-%d')}")
      
      # Generate forecast
      forecast = self.model.predict(future)
      
      # Extract predictions
      future_forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
      future_forecast.columns = ['date', 'predicted_price', 'lower_bound', 'upper_bound']
      
      self.forecast = future_forecast
      
      print(f"✅ Price forecast generated for {start_date.strftime('%Y-%m-%d')} to {future_dates[-1].strftime('%Y-%m-%d')}")
      print(f"💰 Predicted price range: ₹{future_forecast['lower_bound'].min():.0f} - ₹{future_forecast['upper_bound'].max():.0f}/kg")
      
      return future_forecast

    
    def get_sell_recommendation(self, current_price=None, days_ahead=30, start_date=None):
        """Generate AI-powered sell/hold recommendation"""
        self.forecast_prices(days_ahead, start_date)  # ✅ Pass start_date
    
        forecast_df = self.forecast.copy()
        
        # Current price (use latest forecast if not provided)
        if current_price is None:
            current_price = forecast_df.iloc[0]['predicted_price']
        
        # Find optimal selling window (highest predicted price)
        best_day_idx = forecast_df['predicted_price'].idxmax()
        best_day = forecast_df.loc[best_day_idx]
        
        # Calculate potential gains
        potential_gain = best_day['predicted_price'] - current_price
        gain_percentage = (potential_gain / current_price) * 100
        
        # Decision logic
        threshold = 2.0  # Minimum 2% gain to recommend holding
        
        if gain_percentage > threshold:
            action = "HOLD"
            reason = f"Price expected to increase by ₹{potential_gain:.0f}/kg ({gain_percentage:.1f}%)"
        else:
            action = "SELL"
            reason = f"Current price is near optimal (max gain: {gain_percentage:.1f}%)"
        
        recommendation = {
            'action': action,
            'reason': reason,
            'current_price_estimate': current_price,
            'optimal_price_estimate': best_day['predicted_price'],
            'potential_gain_rs_per_kg': potential_gain,
            'potential_gain_percentage': gain_percentage,
            'optimal_sell_date': best_day['date'],
            'confidence_interval': f"₹{best_day['lower_bound']:.0f} - ₹{best_day['upper_bound']:.0f}",
            'days_to_wait': (pd.to_datetime(best_day['date']) - pd.to_datetime(forecast_df.iloc[0]['date'])).days
        }
        
        return recommendation
    
    def save_model(self, model_path):
        """Save trained model for production use"""
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"💾 Model saved to: {model_path}")
    
    def load_model(self, model_path):
        """Load pre-trained model"""
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        print(f"📁 Model loaded from: {model_path}")
