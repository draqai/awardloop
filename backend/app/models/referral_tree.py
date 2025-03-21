from app import db
from datetime import datetime
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

class ReferralTree:
    # Collection name
    collection = 'referral_tree'
    
    @classmethod
    def find_by_id(cls, tree_id):
        """Find a referral relationship by its ID"""
        if isinstance(tree_id, str):
            # Convert string ID to ObjectId if needed
            try:
                tree_id = ObjectId(tree_id)
            except:
                pass
                
        tree_data = db[cls.collection].find_one({'_id': tree_id})
        return cls(tree_data) if tree_data else None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """Find a referral relationship by user ID"""
        if isinstance(user_id, str):
            # Try to convert to ObjectId if it's a string
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        tree_data = db[cls.collection].find_one({'user_id': user_id})
        return cls(tree_data) if tree_data else None
    
    @classmethod
    def find_referrals(cls, referrer_id):
        """Find all users referred by a specific referrer"""
        if isinstance(referrer_id, str):
            # Try to convert to ObjectId if it's a string
            try:
                referrer_id = ObjectId(referrer_id)
            except:
                pass
                
        referrals = db[cls.collection].find({'referrer_id': referrer_id})
        return [cls(ref_data) for ref_data in referrals]
    
    def __init__(self, data=None):
        # Default values
        self._id = None
        self.user_id = None
        self.referrer_id = None
        self.tree_level = 1
        self.tree_position = 0
        self.created_at = datetime.utcnow()
        self.formatted_referrer_id = None
        
        # Apply data if provided
        if data:
            for key, value in data.items():
                setattr(self, key, value)
    
    @property
    def id(self):
        """Property to maintain backward compatibility with SQLAlchemy model"""
        return self._id
    
    def save(self):
        """Save referral relationship to the database"""
        data = self.to_mongo()
        
        if self._id:
            # Update existing relationship
            result = db[self.collection].update_one(
                {'_id': self._id},
                {'$set': data}
            )
            return result.modified_count > 0
        else:
            # Create new relationship
            data['created_at'] = datetime.utcnow()
            try:
                result = db[self.collection].insert_one(data)
                self._id = result.inserted_id
                return True
            except DuplicateKeyError:
                return False
    
    def to_mongo(self):
        """Convert referral tree object to MongoDB document format"""
        data = {
            'user_id': self.user_id,
            'referrer_id': self.referrer_id,
            'tree_level': self.tree_level,
            'tree_position': self.tree_position,
            'formatted_referrer_id': self.formatted_referrer_id
        }
        
        # Only include _id if it exists
        if self._id:
            data['_id'] = self._id
            
        return data
    
    def get_user(self):
        """Get the user for this referral relationship"""
        from app.models.user import User
        return User.find_by_id(self.user_id)
    
    def get_referrer(self):
        """Get the referrer for this relationship"""
        if not self.referrer_id:
            return None
            
        from app.models.user import User
        return User.find_by_id(self.referrer_id)
    
    def __repr__(self):
        return f"<ReferralTree user_id={self.user_id}, referrer_id={self.referrer_id}>"

    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the referral_tree collection"""
        db[cls.collection].create_index('user_id', unique=True)
        db[cls.collection].create_index('referrer_id')