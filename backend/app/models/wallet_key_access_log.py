# app/models/wallet_key_access_log.py
from app import db
from datetime import datetime

class WalletKeyAccessLog(db.Model):
    """
    Model for logging access to encrypted wallet keys.
    """
    __tablename__ = 'wallet_key_access_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_wallet_id = db.Column(db.Integer, db.ForeignKey('user_wallets.id'), nullable=False)
    accessed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    access_reason = db.Column(db.String(255), nullable=False)
    access_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    was_successful = db.Column(db.Boolean, default=False)
    
    # Define relationships
    wallet = db.relationship('UserWallet', backref='access_logs')
    user = db.relationship('User', backref='key_access_logs')
    
    def __repr__(self):
        return f"<WalletKeyAccess wallet_id={self.user_wallet_id} by user_id={self.accessed_by}>"