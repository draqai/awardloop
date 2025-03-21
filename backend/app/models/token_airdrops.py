# app/models/token_airdrops.py
from app import db
from datetime import datetime

class TokenAirdrop(db.Model):
    __tablename__ = 'token_airdrops'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    wallet_address = db.Column(db.String(42), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    tx_hash = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Enum('pending', 'completed', 'failed'), default='pending')
    airdrop_type = db.Column(db.Enum('social_media', 'referral', 'promotion'), default='social_media')
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'wallet_address': self.wallet_address,
            'amount': float(self.amount),
            'tx_hash': self.tx_hash,
            'status': self.status,
            'airdrop_type': self.airdrop_type,
            'reason': self.reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        }