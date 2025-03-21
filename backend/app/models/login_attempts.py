# app/models/login_attempts.py
from app import db
from datetime import datetime

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), nullable=False)
    attempt_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=False)
    is_successful = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<LoginAttempt {self.wallet_address} at {self.attempt_time}>"