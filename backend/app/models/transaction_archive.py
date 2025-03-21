# app/models/transaction_archive.py
from app import db
from datetime import datetime

class TransactionArchive(db.Model):
    """
    Model for archiving completed or failed transactions.
    Stores a copy of PendingTransaction records that have been processed.
    """
    __tablename__ = 'transaction_archives'
    
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, nullable=False)  # Original ID from pending_transactions
    source_wallet_id = db.Column(db.Integer, nullable=True)
    destination_address = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # 'roi', 'referral', etc.
    reference_id = db.Column(db.String(100))  # Investment ID, etc.
    status = db.Column(db.String(20), nullable=False)  # 'completed' or 'failed'
    created_at = db.Column(db.DateTime, nullable=False)  # Original creation time
    processed_at = db.Column(db.DateTime, nullable=True)  # When it was processed
    blockchain_tx_hash = db.Column(db.String(255), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)  # When it was archived
    
    def __repr__(self):
        return f"<TransactionArchive {self.id} - original:{self.original_id} - {self.status}>"