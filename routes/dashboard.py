from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Pool, PoolMembership, Forecast
from datetime import datetime, timedelta
import json
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        # Fetch admin-wide stats
        admin_stats = {
            'total_users': db.session.query(func.count(User.id)).filter(User.role == 'user').scalar() or 0,
            'total_pools': db.session.query(func.count(Pool.id)).scalar() or 0,
            'total_forecasts': db.session.query(func.count(Forecast.id)).scalar() or 0,
            'total_quantity': db.session.query(func.sum(Pool.current_quantity)).scalar() or 0
        }
        # You may want to also fetch all pools, forecasts, etc. for admin management UIs
        return render_template(
            'dashboard.html',
            admin_stats=admin_stats,
            stats=None,                # No personal stats in admin view
            pool_details=None,         # Populate if you want admin to see
            recent_activity=Forecast.query.order_by(Forecast.created_at.desc()).limit(10).all(),
            recent_forecasts=None
        )

    # Normal user dashboard (your current logic):
    user_pools = db.session.query(PoolMembership).filter_by(user_id=current_user.id).all()
    user_forecasts = db.session.query(Forecast).filter_by(user_id=current_user.id).order_by(Forecast.created_at.desc()).limit(5).all()
    
    total_quantity = sum([membership.quantity_contributed for membership in user_pools])
    active_pools = len([p for p in user_pools if p.status == 'active'])
    total_forecasts = db.session.query(Forecast).filter_by(user_id=current_user.id).count()
    
    avg_gain = 0
    if user_forecasts:
        avg_gain = sum([f.potential_gain for f in user_forecasts]) / len(user_forecasts)
    
    pool_details = []
    for membership in user_pools:
        pool = db.session.query(Pool).filter_by(id=membership.pool_id).first()
        if pool:
            pool_details.append({
                'membership': membership,
                'pool': pool,
                'progress': (pool.current_quantity / pool.target_quantity) * 100 if pool.target_quantity else 0,
                'estimated_value': membership.quantity_contributed * pool.target_price,
                'extra_earnings': membership.quantity_contributed * (pool.target_price - 2800)
            })
    
    stats = {
        'active_pools': active_pools,
        'total_quantity': total_quantity,
        'total_forecasts': total_forecasts,
        'avg_potential_gain': avg_gain
    }
    
    return render_template(
        'dashboard.html', 
        stats=stats, 
        pool_details=pool_details,
        recent_forecasts=user_forecasts,
        admin_stats=None
    )
