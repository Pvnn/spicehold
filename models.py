from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(100))
    farm_size = db.Column(db.Float)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pools_created = db.relationship('Pool', backref='creator', lazy='dynamic')
    pool_memberships = db.relationship('PoolMembership', backref='user', lazy='dynamic')
    forecasts = db.relationship('Forecast', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_quantity = db.Column(db.Integer, nullable=False)
    current_quantity = db.Column(db.Integer, default=0)
    target_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')
    deadline = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    memberships = db.relationship('PoolMembership', backref='pool', lazy='dynamic')

class PoolMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'), nullable=False)
    quantity_contributed = db.Column(db.Integer, nullable=False)
    join_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

class Forecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    optimal_price = db.Column(db.Float, nullable=False)
    action = db.Column(db.String(20), nullable=False)
    potential_gain = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
