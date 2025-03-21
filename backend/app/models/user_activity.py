# app/models/user_activity.py
from app import db
from datetime import datetime

class UserActivity(db.Model):
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    activity_description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationship
    user = db.relationship('User', backref='activities')
    
    def __repr__(self):
        return f"<UserActivity {self.activity_type} by user_id={self.user_id}>"