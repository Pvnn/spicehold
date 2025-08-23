import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'spicehold-secret-key-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///spicehold.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
