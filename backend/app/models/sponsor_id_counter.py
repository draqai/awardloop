# app/models/sponsor_id_counter.py
from app import db

class SponsorIdCounter(db.Model):
    __tablename__ = 'sponsor_id_counter'
    
    id = db.Column(db.Integer, primary_key=True, default=1)
    current_value = db.Column(db.Integer, nullable=False, default=0)
    prefix = db.Column(db.String(5), nullable=False, default='AL')
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f"<SponsorIdCounter current={self.current_value}>"