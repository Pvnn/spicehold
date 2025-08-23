# src/user_data.py
import pandas as pd
import os
from datetime import datetime, timedelta
import streamlit as st

# File paths
USERS_FILE = "data/users.csv"
POOLS_FILE = "data/pools.csv" 
MEMBERSHIPS_FILE = "data/pool_memberships.csv"
FORECASTS_FILE = "data/user_forecasts.csv"
BUYERS_FILE = "data/buyers.csv"

def ensure_data_files():
    """Ensure all data files exist"""
    files_to_check = [USERS_FILE, POOLS_FILE, MEMBERSHIPS_FILE, FORECASTS_FILE]
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            # Create empty DataFrame with proper columns
            if 'users.csv' in file_path:
                pd.DataFrame(columns=['username', 'name', 'email', 'location', 'phone', 'farm_size', 'created_date']).to_csv(file_path, index=False)
            elif 'pools.csv' in file_path:
                pd.DataFrame(columns=['pool_id', 'pool_name', 'target_quantity', 'current_quantity', 'target_price', 'status', 'deadline', 'created_by', 'created_date']).to_csv(file_path, index=False)
            elif 'memberships.csv' in file_path:
                pd.DataFrame(columns=['username', 'pool_id', 'quantity_contributed', 'join_date', 'status']).to_csv(file_path, index=False)
            elif 'forecasts.csv' in file_path:
                pd.DataFrame(columns=['username', 'forecast_date', 'current_price', 'optimal_price', 'action', 'potential_gain', 'created_at']).to_csv(file_path, index=False)

def get_user_profile(username):
    """Get user profile information"""
    try:
        users_df = pd.read_csv(USERS_FILE)
        user_data = users_df[users_df['username'] == username]
        if not user_data.empty:
            return user_data.iloc[0].to_dict()
        return None
    except:
        return None

def get_user_pools(username):
    """Get pools user has joined"""
    try:
        memberships_df = pd.read_csv(MEMBERSHIPS_FILE)
        pools_df = pd.read_csv(POOLS_FILE)
        
        user_memberships = memberships_df[memberships_df['username'] == username]
        if user_memberships.empty:
            return pd.DataFrame()
            
        # Join with pools data
        user_pools = user_memberships.merge(pools_df, on='pool_id', how='left')
        return user_pools
    except:
        return pd.DataFrame()

def get_all_active_pools():
    """Get all active pools"""
    try:
        pools_df = pd.read_csv(POOLS_FILE)
        return pools_df[pools_df['status'] == 'active']
    except:
        return pd.DataFrame()

def join_pool(username, pool_id, quantity):
    """User joins a pool"""
    try:
        # Check if user already in pool
        memberships_df = pd.read_csv(MEMBERSHIPS_FILE)
        existing = memberships_df[(memberships_df['username'] == username) & (memberships_df['pool_id'] == pool_id)]
        
        if not existing.empty:
            return False, "You're already in this pool!"
        
        # Add membership
        new_membership = {
            'username': username,
            'pool_id': pool_id,
            'quantity_contributed': quantity,
            'join_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'active'
        }
        
        memberships_df = pd.concat([memberships_df, pd.DataFrame([new_membership])], ignore_index=True)
        memberships_df.to_csv(MEMBERSHIPS_FILE, index=False)
        
        # Update pool current quantity
        pools_df = pd.read_csv(POOLS_FILE)
        pools_df.loc[pools_df['pool_id'] == pool_id, 'current_quantity'] += quantity
        pools_df.to_csv(POOLS_FILE, index=False)
        
        return True, "Successfully joined pool!"
    
    except Exception as e:
        return False, f"Error joining pool: {str(e)}"

def create_pool(username, pool_name, target_quantity, target_price, deadline):
    """Create a new pool"""
    try:
        pools_df = pd.read_csv(POOLS_FILE)
        
        # Get next pool ID
        next_id = pools_df['pool_id'].max() + 1 if not pools_df.empty else 1
        
        new_pool = {
            'pool_id': next_id,
            'pool_name': pool_name,
            'target_quantity': target_quantity,
            'current_quantity': 0,
            'target_price': target_price,
            'status': 'active',
            'deadline': deadline,
            'created_by': username,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        pools_df = pd.concat([pools_df, pd.DataFrame([new_pool])], ignore_index=True)
        pools_df.to_csv(POOLS_FILE, index=False)
        
        return True, next_id, "Pool created successfully!"
    
    except Exception as e:
        return False, None, f"Error creating pool: {str(e)}"

def save_user_forecast(username, forecast_data):
    """Save user's price forecast"""
    try:
        forecasts_df = pd.read_csv(FORECASTS_FILE)
        
        forecast_record = {
            'username': username,
            'forecast_date': forecast_data['optimal_sell_date'],
            'current_price': forecast_data['current_price_estimate'],
            'optimal_price': forecast_data['optimal_price_estimate'],
            'action': forecast_data['action'],
            'potential_gain': forecast_data['potential_gain_rs_per_kg'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        forecasts_df = pd.concat([forecasts_df, pd.DataFrame([forecast_record])], ignore_index=True)
        forecasts_df.to_csv(FORECASTS_FILE, index=False)
        
        return True
    except Exception as e:
        st.error(f"Error saving forecast: {str(e)}")
        return False

def get_user_forecasts(username):
    """Get user's forecast history"""
    try:
        forecasts_df = pd.read_csv(FORECASTS_FILE)
        return forecasts_df[forecasts_df['username'] == username]
    except:
        return pd.DataFrame()

def get_user_dashboard_stats(username):
    """Get user dashboard statistics"""
    try:
        user_pools = get_user_pools(username)
        user_forecasts = get_user_forecasts(username)
        
        stats = {
            'pools_joined': len(user_pools),
            'active_pools': len(user_pools[user_pools['status'] == 'active']),
            'total_quantity': user_pools['quantity_contributed'].sum() if not user_pools.empty else 0,
            'forecasts_made': len(user_forecasts),
            'avg_potential_gain': user_forecasts['potential_gain'].mean() if not user_forecasts.empty else 0
        }
        
        return stats
    except:
        return {
            'pools_joined': 0,
            'active_pools': 0, 
            'total_quantity': 0,
            'forecasts_made': 0,
            'avg_potential_gain': 0
        }
