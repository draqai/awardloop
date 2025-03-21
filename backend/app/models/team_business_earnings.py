from app import db
import datetime

class TeamBusinessEarnings(db.Model):
    """
    Model for tracking team business earnings
    Records rewards earned based on team business volume and rank level
    """
    __tablename__ = 'team_business_earnings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    rank_level = db.Column(db.Integer, default=1)
    business_volume = db.Column(db.Numeric(10, 2), default=0.00)
    status = db.Column(db.Enum('pending', 'processed', 'failed'), default='pending')
    distribution_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    transaction_id = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('team_business_earnings', lazy=True))
    
    def __repr__(self):
        return f"<TeamBusinessEarnings id={self.id} user_id={self.user_id} amount={self.amount} rank_level={self.rank_level}>"
    
    @classmethod
    def get_user_earnings(cls, user_id, status=None):
        """Get earnings for a specific user, optionally filtered by status"""
        query = cls.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.all()
    
    @classmethod
    def get_pending_earnings(cls):
        """Get all pending team business earnings"""
        return cls.query.filter_by(status='pending').all()
    
    @classmethod
    def process_earnings(cls, earning_id):
        """Mark a team business earning as processed"""
        earning = cls.query.get(earning_id)
        if earning and earning.status == 'pending':
            earning.status = 'processed'
            earning.updated_at = datetime.datetime.utcnow()
            db.session.commit()
            return True
        return False