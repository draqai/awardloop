from flask_jwt_extended import create_access_token
from app.models.user import User
from datetime import datetime, timedelta
import secrets

class AuthService:
    @staticmethod
    def generate_token(user):
        """Generate JWT token for user"""
        # Use string ID instead of dict for the identity
        # This works better with Flask-JWT-Extended's default configuration
        return create_access_token(identity=str(user.id))
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token (handled by Flask-JWT-Extended)"""
        # This is mostly handled by the @jwt_required() decorator
        # Custom verification logic can be added here if needed
        pass
    
    @staticmethod
    def generate_reset_token():
        """Generate a secure token for PIN reset"""
        return secrets.token_hex(32)