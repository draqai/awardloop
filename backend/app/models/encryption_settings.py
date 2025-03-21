# app/models/encryption_settings.py
from app import db
from datetime import datetime

class EncryptionSettings(db.Model):
    """
    Model for storing encryption configuration settings.
    """
    __tablename__ = 'encryption_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EncryptionSetting {self.setting_key}>"
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by key"""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default
    
    @classmethod
    def update_setting(cls, key, value, description=None):
        """Update or create a setting"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=value,
                description=description
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting

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