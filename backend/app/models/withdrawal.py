from app import db
import datetime

class Withdrawal(db.Model):
    """
    Model for tracking withdrawal requests
    """
    __tablename__ = 'withdrawals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    wallet_address = db.Column(db.String(255), nullable=False)
    withdrawal_status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed'), 
                                default='pending', nullable=False)
    blockchain_tx_id = db.Column(db.String(255))
    admin_id = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, 
                          onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Withdrawal {self.id}: {self.amount} USDT by user {self.user_id}>"