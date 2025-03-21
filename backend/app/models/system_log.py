# app/models/system_log.py
from app import db
from datetime import datetime
from bson.objectid import ObjectId

class SystemLog:
    """
    System log model for MongoDB.
    Stores system logs such as automated actions, errors, and important system events.
    """
    
    def __init__(self, log_type=None, log_message=None):
        """
        Initialize a new system log entry
        
        Args:
            log_type (str): Type of log entry (e.g. 'bid_cycle_auto_reopened', 'balance_sync')
            log_message (str): Detailed log message
        """
        self.log_type = log_type
        self.log_message = log_message
        self.created_at = datetime.utcnow()
        self._id = None
    
    def save(self):
        """Save the system log to MongoDB"""
        doc = {
            'log_type': self.log_type,
            'log_message': self.log_message,
            'created_at': self.created_at
        }
        result = db.system_log.insert_one(doc)
        self._id = result.inserted_id
        return self._id
    
    @classmethod
    def find_by_id(cls, log_id):
        """Find a system log by its ID"""
        if isinstance(log_id, str):
            try:
                log_id = ObjectId(log_id)
            except:
                return None
        return db.system_log.find_one({'_id': log_id})
    
    @classmethod
    def find_all(cls, limit=100, sort_by='created_at', sort_direction=-1):
        """
        Get all system logs with optional sorting and limit
        
        Args:
            limit (int): Maximum number of logs to return
            sort_by (str): Field to sort by
            sort_direction (int): 1 for ascending, -1 for descending
        """
        return list(db.system_log.find().sort(sort_by, sort_direction).limit(limit))
    
    @classmethod
    def find_by_type(cls, log_type, limit=100):
        """Find system logs by type with optional limit"""
        return list(db.system_log.find({'log_type': log_type}).sort('created_at', -1).limit(limit))
    
    def __repr__(self):
        """String representation of the log entry"""
        message_preview = self.log_message[:30] + "..." if self.log_message and len(self.log_message) > 30 else self.log_message
        return f"<SystemLog {self.log_type}: {message_preview}>"