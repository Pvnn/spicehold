from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Pool, PoolMembership, Forecast
from config import Config
from datetime import datetime, timedelta
import json
from src.models.price_forecaster import CardamomPriceForecaster

# Instantiate and load the forecasting model ONCE
forecaster = CardamomPriceForecaster('data/processed/clean_auction_data.csv')
forecaster.load_model('data/models/cardamom_price_model.pkl')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Login manager setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.forecast import forecast_bp
    from routes.pools import pools_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(forecast_bp)
    app.register_blueprint(pools_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create demo users if they don't exist
        if not User.query.filter_by(username='raman_kumar').first():
            demo_users = [
                {'username': 'raman_kumar', 'email': 'raman@gmail.com', 'name': 'Raman Kumar', 'location': 'Kumily', 'farm_size': 2.5},
                {'username': 'priya_nair', 'email': 'priya@gmail.com', 'name': 'Priya Nair', 'location': 'Thekkady', 'farm_size': 1.8},
                {'username': 'demo_farmer', 'email': 'demo@spicehold.com', 'name': 'Demo Farmer', 'location': 'Vandanmedu', 'farm_size': 3.0}
            ]
            
            for user_data in demo_users:
                user = User(**user_data)
                user.set_password('password123')
                db.session.add(user)
            
            db.session.commit()
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('auth.login'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
