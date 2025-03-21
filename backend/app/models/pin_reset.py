# app/models/pin_reset.py
from app import db
from datetime import datetime

class PinReset(db.Model):
    """
    Model for storing PIN reset tokens
    
    This model tracks PIN reset tokens, expiration dates, and associates them with users
    """
    __tablename__ = 'pin_reset_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wallet_address = db.Column(db.String(42), nullable=False)
    reset_token = db.Column(db.String(64), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('pin_resets', lazy=True))
    
    @property
    def is_expired(self):
        """Check if the reset token has expired"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<PinReset token for user_id: {self.user_id}, expires: {self.expires_at}>"