from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Pool, PoolMembership, User
from datetime import datetime, timedelta
import pandas as pd

pools_bp = Blueprint('pools', __name__)

def get_exporter_recommendations(pool):
    """Mock exporter recommendations"""
    exporters = [
        {'name': 'Kerala Spices Export', 'location': 'Kochi', 'price_per_kg': 3400, 'payment_days': 15, 'reputation': 92, 'score': 0.89},
        {'name': 'Global Spice Traders', 'location': 'Dubai', 'price_per_kg': 3550, 'payment_days': 21, 'reputation': 95, 'score': 0.91},
        {'name': 'South India Exporters', 'location': 'Chennai', 'price_per_kg': 3300, 'payment_days': 10, 'reputation': 85, 'score': 0.82},
        {'name': 'Premium Cardamom Co.', 'location': 'Kumily', 'price_per_kg': 3250, 'payment_days': 7, 'reputation': 88, 'score': 0.78},
    ]
    
    # Sort by score (descending)
    return sorted(exporters, key=lambda x: x['score'], reverse=True)

@pools_bp.route('/pools')
@login_required
def pools():
    # Get all active pools
    active_pools = db.session.query(Pool).filter_by(status='active').all()
    
    # Get user's pool memberships
    user_memberships = db.session.query(PoolMembership).filter_by(user_id=current_user.id).all()
    user_pool_ids = [m.pool_id for m in user_memberships]
    
    # Add progress and membership info to pools
    pools_data = []
    for pool in active_pools:
        progress = (pool.current_quantity / pool.target_quantity) * 100
        is_member = pool.id in user_pool_ids
        user_contribution = 0
        
        if is_member:
            membership = next(m for m in user_memberships if m.pool_id == pool.id)
            user_contribution = membership.quantity_contributed
        
        pools_data.append({
            'pool': pool,
            'progress': min(progress, 100),
            'is_member': is_member,
            'user_contribution': user_contribution,
            'members_count': db.session.query(PoolMembership).filter_by(pool_id=pool.id).count(),
            'creator_name': db.session.query(User).filter_by(id=pool.creator_id).first().name
        })
    
    # Get user's pools with exporter recommendations
    user_pools_data = []
    for membership in user_memberships:
        pool = db.session.query(Pool).filter_by(id=membership.pool_id).first()
        if pool:
            progress = (pool.current_quantity / pool.target_quantity) * 100
            exporters = []
            
            # Show exporters if pool is 80% full
            if progress >= 80:
                exporters = get_exporter_recommendations(pool)[:3]
            
            user_pools_data.append({
                'membership': membership,
                'pool': pool,
                'progress': progress,
                'exporters': exporters
            })
    
    default_deadline = (datetime.utcnow() + timedelta(days=7)).strftime('%Y-%m-%d')

    return render_template('pools.html', 
                          active_pools=pools_data,
                          user_pools=user_pools_data,
                          default_deadline=default_deadline)

@pools_bp.route('/join_pool', methods=['POST'])
@login_required
def join_pool():
    pool_id = int(request.form['pool_id'])
    quantity = int(request.form['quantity'])
    
    # Check if user already in pool
    existing_membership = db.session.query(PoolMembership).filter_by(
        user_id=current_user.id, 
        pool_id=pool_id
    ).first()
    
    if existing_membership:
        flash('You are already a member of this pool!', 'error')
        return redirect(url_for('pools.pools'))
    
    # Get pool
    pool = db.session.query(Pool).filter_by(id=pool_id).first()
    if not pool:
        flash('Pool not found!', 'error')
        return redirect(url_for('pools.pools'))
    
    # Check if pool has capacity
    if pool.current_quantity + quantity > pool.target_quantity:
        flash(f'Pool only has capacity for {pool.target_quantity - pool.current_quantity} kg more!', 'error')
        return redirect(url_for('pools.pools'))
    
    # Create membership
    membership = PoolMembership(
        user_id=current_user.id,
        pool_id=pool_id,
        quantity_contributed=quantity,
        join_date=datetime.utcnow().date()
    )
    
    # Update pool quantity
    pool.current_quantity += quantity
    
    db.session.add(membership)
    db.session.commit()
    
    flash(f'🎉 Successfully joined {pool.name} with {quantity} kg!', 'success')
    return redirect(url_for('pools.pools'))

@pools_bp.route('/create_pool', methods=['POST'])
@login_required
def create_pool():
    pool_name = request.form['pool_name']
    target_quantity = int(request.form['target_quantity'])
    target_price = float(request.form['target_price'])
    deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
    
    # Create pool
    new_pool = Pool(
        name=pool_name,
        target_quantity=target_quantity,
        target_price=target_price,
        deadline=deadline,
        creator_id=current_user.id
    )
    
    db.session.add(new_pool)
    db.session.commit()
    
    flash(f'✅ Pool "{pool_name}" created successfully! Pool ID: {new_pool.id}', 'success')
    return redirect(url_for('pools.pools'))

@pools_bp.route('/select_exporter', methods=['POST'])
@login_required
def select_exporter():
    pool_id = int(request.form['pool_id'])
    exporter_name = request.form['exporter_name']
    
    # Get pool and user's membership
    pool = db.session.query(Pool).filter_by(id=pool_id).first()
    membership = db.session.query(PoolMembership).filter_by(
        user_id=current_user.id,
        pool_id=pool_id
    ).first()
    
    if not pool or not membership:
        flash('Pool or membership not found!', 'error')
        return redirect(url_for('pools.pools'))
    
    # Mock deal confirmation
    flash(f'🎉 Deal confirmed with {exporter_name}! Your contribution: {membership.quantity_contributed} kg', 'success')
    return redirect(url_for('pools.pools'))
