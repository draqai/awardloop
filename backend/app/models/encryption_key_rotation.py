# app/models/encryption_key_rotation.py
from app import db
from datetime import datetime

class EncryptionKeyRotation(db.Model):
    """
    Model for tracking encryption key rotation history.
    """
    __tablename__ = 'encryption_key_rotation'
    
    id = db.Column(db.Integer, primary_key=True)
    key_identifier = db.Column(db.String(64), unique=True, nullable=False)
    rotation_date = db.Column(db.DateTime, default=datetime.utcnow)
    rotated_by = db.Column(db.String(100), nullable=True)
    affected_records = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'failed'), default='pending')
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<KeyRotation {self.key_identifier} ({self.status})>"