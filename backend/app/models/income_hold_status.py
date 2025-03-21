# app/models/income_hold_status.py
from app import db
from datetime import datetime
from bson import ObjectId

class IncomeHoldStatus:
    """
    IncomeHoldStatus model for MongoDB
    
    Tracks income hold status for users (whether certain income types are on hold)
    """
    
    COLLECTION = 'income_hold_status'
    
    def __init__(self, user_id, level_income_on_hold=False, team_rewards_on_hold=False,
                 initial_unit_count=0, last_purchase_date=None, updated_at=None, id=None):
        """
        Initialize a new IncomeHoldStatus instance
        
        Args:
            user_id (int or ObjectId): The ID of the user
            level_income_on_hold (bool, optional): Whether level income is on hold. Defaults to False.
            team_rewards_on_hold (bool, optional): Whether team rewards are on hold. Defaults to False.
            initial_unit_count (int, optional): Initial unit count. Defaults to 0.
            last_purchase_date (datetime, optional): Date of last purchase. Defaults to None.
            updated_at (datetime, optional): Last update timestamp. Defaults to current UTC time.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.user_id = user_id
        self.level_income_on_hold = level_income_on_hold
        self.team_rewards_on_hold = team_rewards_on_hold
        self.initial_unit_count = initial_unit_count
        self.last_purchase_date = last_purchase_date
        self.updated_at = updated_at or datetime.utcnow()
    
    def __repr__(self):
        return f"<IncomeHoldStatus user_id={self.user_id}, level_hold={self.level_income_on_hold}, team_hold={self.team_rewards_on_hold}>"
    
    def to_dict(self):
        """
        Convert the IncomeHoldStatus object to a dictionary
        
        Returns:
            dict: Dictionary representation of the IncomeHoldStatus
        """
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "level_income_on_hold": self.level_income_on_hold,
            "team_rewards_on_hold": self.team_rewards_on_hold,
            "initial_unit_count": self.initial_unit_count,
            "last_purchase_date": self.last_purchase_date,
            "updated_at": self.updated_at
        }
    
    def save(self):
        """
        Save the IncomeHoldStatus object to the database
        
        Returns:
            ObjectId: The ID of the inserted or updated document
        """
        data = self.to_dict()
        
        if self.id:
            # Update existing document
            data.pop("_id", None)  # Remove _id for update operation
            result = db[self.COLLECTION].update_one(
                {"_id": self.id},
                {"$set": data}
            )
            return self.id
        else:
            # Insert new document
            data.pop("_id", None)  # Remove None _id for insert
            result = db[self.COLLECTION].insert_one(data)
            self.id = result.inserted_id
            return self.id
    
    @classmethod
    def find_by_id(cls, status_id):
        """
        Find an IncomeHoldStatus by ID
        
        Args:
            status_id (str or ObjectId): The ID of the IncomeHoldStatus to find
            
        Returns:
            IncomeHoldStatus or None: The found IncomeHoldStatus object or None if not found
        """
        if isinstance(status_id, str):
            status_id = ObjectId(status_id)
            
        data = db[cls.COLLECTION].find_one({"_id": status_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """
        Find an IncomeHoldStatus by user ID
        
        Args:
            user_id (int or ObjectId): The ID of the user
            
        Returns:
            IncomeHoldStatus or None: The found IncomeHoldStatus object or None if not found
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        data = db[cls.COLLECTION].find_one({"user_id": user_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_users_with_hold(cls, income_type='level'):
        """
        Find all users with a specific income type on hold
        
        Args:
            income_type (str, optional): Type of income hold to filter by ('level' or 'team'). Defaults to 'level'.
            
        Returns:
            list: List of IncomeHoldStatus objects for users with hold
        """
        field = "level_income_on_hold" if income_type == 'level' else "team_rewards_on_hold"
        cursor = db[cls.COLLECTION].find({field: True})
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create an IncomeHoldStatus object from a dictionary
        
        Args:
            data (dict): Dictionary representing an IncomeHoldStatus document
            
        Returns:
            IncomeHoldStatus: An IncomeHoldStatus object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            level_income_on_hold=data.get("level_income_on_hold", False),
            team_rewards_on_hold=data.get("team_rewards_on_hold", False),
            initial_unit_count=data.get("initial_unit_count", 0),
            last_purchase_date=data.get("last_purchase_date"),
            updated_at=data.get("updated_at")
        )
    
    @classmethod
    def get_user(cls, status_id):
        """
        Get the user associated with this income hold status
        
        Args:
            status_id (str or ObjectId): ID of the IncomeHoldStatus
            
        Returns:
            User or None: The associated User object or None
        """
        from app.models.user import User
        
        status = cls.find_by_id(status_id)
        if not status:
            return None
            
        return User.find_by_id(status.user_id)
    
    @classmethod
    def delete_by_id(cls, status_id):
        """
        Delete an IncomeHoldStatus by ID
        
        Args:
            status_id (str or ObjectId): ID of the IncomeHoldStatus to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(status_id, str):
            status_id = ObjectId(status_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": status_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the IncomeHoldStatus collection
        """
        db[cls.COLLECTION].create_index("user_id", unique=True)
        db[cls.COLLECTION].create_index("level_income_on_hold")
        db[cls.COLLECTION].create_index("team_rewards_on_hold")
        db[cls.COLLECTION].create_index("last_purchase_date")