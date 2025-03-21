# app/models/user_legs.py
from app import db
from datetime import datetime

class UserLegs(db.Model):
    __tablename__ = 'user_legs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_legs = db.Column(db.Integer, default=0)
    active_legs = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationship
    user = db.relationship('User', backref='legs_info')
    
    def __repr__(self):
        return f"<UserLegs user_id={self.user_id}, total={self.total_legs}, active={self.active_legs}>"