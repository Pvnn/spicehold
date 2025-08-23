from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Pool, PoolMembership, Forecast
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    user_pools = db.session.query(PoolMembership).filter_by(user_id=current_user.id).all()
    user_forecasts = db.session.query(Forecast).filter_by(user_id=current_user.id).order_by(Forecast.created_at.desc()).limit(5).all()
    
    # Calculate stats
    total_quantity = sum([membership.quantity_contributed for membership in user_pools])
    active_pools = len([p for p in user_pools if p.status == 'active'])
    total_forecasts = db.session.query(Forecast).filter_by(user_id=current_user.id).count()
    
    # Calculate average potential gain
    avg_gain = 0
    if user_forecasts:
        avg_gain = sum([f.potential_gain for f in user_forecasts]) / len(user_forecasts)
    
    # Get pool details
    pool_details = []
    for membership in user_pools:
        pool = db.session.query(Pool).filter_by(id=membership.pool_id).first()
        if pool:
            pool_details.append({
                'membership': membership,
                'pool': pool,
                'progress': (pool.current_quantity / pool.target_quantity) * 100,
                'estimated_value': membership.quantity_contributed * pool.target_price,
                'extra_earnings': membership.quantity_contributed * (pool.target_price - 2800)
            })
    
    stats = {
        'active_pools': active_pools,
        'total_quantity': total_quantity,
        'total_forecasts': total_forecasts,
        'avg_potential_gain': avg_gain
    }
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         pool_details=pool_details,
                         recent_forecasts=user_forecasts)
