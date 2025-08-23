from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from models import db, Forecast
from datetime import datetime, timedelta
import json

from app import forecaster  # Import the loaded model

forecast_bp = Blueprint('forecast', __name__)

@forecast_bp.route('/forecast', methods=['GET', 'POST'])
@login_required
def forecast():
    forecast_data, recommendation = None, None
    
    # Default values for first visit
    default_values = {
        'harvest_date': (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'quantity': 100,
        'storage_quality': 'Excellent (Air-tight, Cool)',
        'forecast_from_date': datetime.utcnow().strftime('%Y-%m-%d')
    }

    if request.method == 'POST':
        # Get form values
        harvest_date = request.form.get('harvest_date', default_values['harvest_date'])
        quantity = int(request.form.get('quantity', default_values['quantity']))
        storage_quality = request.form.get('storage_quality', default_values['storage_quality'])
        forecast_from_date = request.form.get('forecast_from_date', default_values['forecast_from_date'])

        # Store submitted values to redisplay in form
        form_values = {
            'harvest_date': harvest_date,
            'quantity': quantity,
            'storage_quality': storage_quality,
            'forecast_from_date': forecast_from_date
        }

        # Generate forecast using real model
        forecast_df = forecaster.forecast_prices(days_ahead=30, start_date=forecast_from_date)
        forecast_data = {
            'dates': [d.strftime('%Y-%m-%d') for d in forecast_df['date']],
            'prices': list(forecast_df['predicted_price']),
            'labels': [d.strftime('%d %b %Y') for d in forecast_df['date']],   # "14 Sep 2025" format
            'upper': list(forecast_df['upper_bound']),
            'lower': list(forecast_df['lower_bound'])
        }

        recommendation = forecaster.get_sell_recommendation(days_ahead=30, start_date=forecast_from_date)

        # Save to database
        forecast_date = recommendation['optimal_sell_date']
        if isinstance(forecast_date, str):
            forecast_date = datetime.strptime(forecast_date, '%Y-%m-%d').date()

        new_forecast = Forecast(
            user_id=current_user.id,
            forecast_date=forecast_date,
            current_price=recommendation['current_price_estimate'],
            optimal_price=recommendation['optimal_price_estimate'],
            action=recommendation['action'],
            potential_gain=recommendation['potential_gain_rs_per_kg']
        )
        db.session.add(new_forecast)
        db.session.commit()
        
        flash('✅ Forecast generated successfully!', 'success')
    else:
        # On GET request, use default values
        form_values = default_values
        quantity = default_values['quantity']  # Ensure quantity is available

    return render_template('forecast.html',
                         forecast_data=json.dumps(forecast_data) if forecast_data else None,
                         recommendation=recommendation,
                         form_values=form_values,
                         quantity=quantity if 'quantity' in locals() else form_values['quantity'])
