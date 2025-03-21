import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB configuration
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://awardloop_user:8KESTazumOtvEgK2@awardloop.lcuzs.mongodb.net/awardloop'
    
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # Tatum.io configuration
    TATUM_API_KEY = os.environ.get('TATUM_API_KEY')
    TATUM_API_URL = os.environ.get('TATUM_API_URL') or 'https://api.tatum.io/v4'
    
    # Web3 configuration
    WEB3_PROVIDER_URI = os.environ.get('WEB3_PROVIDER_URI') or 'https://bsc-dataseed.binance.org/'