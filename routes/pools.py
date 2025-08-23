from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Pool, PoolMembership
from decorators import admin_required
from datetime import datetime, timedelta

pools_bp = Blueprint('pools', __name__)

@pools_bp.route('/pools')
@login_required
def pools():
    """Display pools based on user role"""
    active_pools = Pool.query.filter_by(status='active').all()
    
    # Prepare pool data with membership info
    pool_data = []
    for pool in active_pools:
        # Check if current user is a member
        membership = PoolMembership.query.filter_by(
            user_id=current_user.id, 
            pool_id=pool.id
        ).first()
        
        progress = (pool.current_quantity / pool.target_quantity) * 100
        
        pool_info = {
            'pool': pool,
            'is_member': membership is not None,
            'user_contribution': membership.quantity_contributed if membership else 0,
            'members_count': pool.memberships.count(),
            'progress': progress,
            'creator_name': pool.creator.name  # Now properly referenced
        }
        pool_data.append(pool_info)
    
    # Get user's pool memberships
    user_pools = []
    if current_user.pool_memberships:
        for membership in current_user.pool_memberships:
            pool = membership.pool
            progress = (pool.current_quantity / pool.target_quantity) * 100
            user_pools.append({
                'pool': pool,
                'membership': membership,
                'progress': progress,
                'exporters': []  # Add exporter logic if needed
            })
    
    return render_template('pools.html', 
                         active_pools=pool_data, 
                         user_pools=user_pools,
                         default_deadline=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))

@pools_bp.route('/pools/create', methods=['POST'])
@login_required
@admin_required  # NEW: Admin only
def create_pool():
    """Create new pool - Admin only"""
    try:
        pool = Pool(
            name=request.form['pool_name'],
            target_quantity=float(request.form['target_quantity']),
            target_price=float(request.form['target_price']),
            deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d').date(),
            creator_id=current_user.id  # NEW: Set creator
        )
        
        db.session.add(pool)
        db.session.commit()
        
        flash('Pool created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating pool: {str(e)}', 'error')
    
    return redirect(url_for('pools.pools'))

@pools_bp.route('/pools/<int:pool_id>/delete', methods=['POST'])
@login_required
@admin_required  # NEW: Admin only
def delete_pool(pool_id):
    """Delete pool - Admin only"""
    try:
        pool = Pool.query.get_or_404(pool_id)
        
        # Check if pool has members
        if pool.memberships.count() > 0:
            flash('Cannot delete pool with existing members', 'error')
            return redirect(url_for('pools.pools'))
        
        db.session.delete(pool)
        db.session.commit()
        
        flash('Pool deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting pool: {str(e)}', 'error')
    
    return redirect(url_for('pools.pools'))

@pools_bp.route('/pools/join', methods=['POST'])
@login_required
def join_pool():
    """Join pool - All users"""
    try:
        pool_id = int(request.form['pool_id'])
        quantity = float(request.form['quantity'])
        
        pool = Pool.query.get_or_404(pool_id)
        
        # Check if user already joined
        existing = PoolMembership.query.filter_by(
            user_id=current_user.id, 
            pool_id=pool_id
        ).first()
        
        if existing:
            flash('You are already a member of this pool', 'warning')
            return redirect(url_for('pools.pools'))
        
        # Check if adding quantity exceeds target
        if pool.current_quantity + quantity > pool.target_quantity:
            flash('Quantity exceeds pool target', 'error')
            return redirect(url_for('pools.pools'))
        
        # Create membership
        membership = PoolMembership(
            user_id=current_user.id,
            pool_id=pool_id,
            quantity_contributed=quantity
        )
        
        # Update pool quantity
        pool.current_quantity += quantity
        
        db.session.add(membership)
        db.session.commit()
        
        flash(f'Successfully joined pool with {quantity}kg!', 'success')
        
    except Exception as e:
        flash(f'Error joining pool: {str(e)}', 'error')
    
    return redirect(url_for('pools.pools'))
