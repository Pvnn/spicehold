from price_forecaster import CardamomPriceForecaster
from prophet.diagnostics import cross_validation, performance_metrics
import itertools

def tune_prophet_hyperparams():
    forecaster = CardamomPriceForecaster('data/processed/clean_auction_data.csv')
    data = forecaster.load_and_prepare_data()
    train_data, _ = forecaster.split_data(data)
    
    param_grid = {
        'changepoint_prior_scale': [0.01, 0.05, 0.1],
        'seasonality_prior_scale': [5, 10, 15]
    }
    
    best_params = None
    best_mape = float('inf')
    
    for cps, sps in itertools.product(param_grid['changepoint_prior_scale'], 
                                      param_grid['seasonality_prior_scale']):
        print(f"Testing: cps={cps}, sps={sps}")
        
        model = forecaster.create_prophet_model()
        model.changepoint_prior_scale = cps
        model.seasonality_prior_scale = sps
        model.fit(train_data)
        
        # Fixed cross-validation parameters - all in days
        df_cv = cross_validation(model, initial='730 days', period='90 days', horizon='90 days')
        df_p = performance_metrics(df_cv)
        mean_mape = df_p['mape'].mean()
        
        print(f"MAPE: {mean_mape:.3f}")
        
        if mean_mape < best_mape:
            best_mape = mean_mape
            best_params = {'changepoint_prior_scale': cps, 'seasonality_prior_scale': sps}
    
    print(f"🎯 Best params: {best_params} with MAPE={best_mape:.3f}")
    return best_params

# Run tuning
best_params = tune_prophet_hyperparams()
