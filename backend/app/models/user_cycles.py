# app/models/user_cycles.py
from app import db
from datetime import datetime
from bson import ObjectId
from decimal import Decimal

class UserCycle:
    """
    UserCycle model for MongoDB
    
    Tracks user participation in bid cycles
    """
    
    COLLECTION = 'user_cycles'
    
    def __init__(self, user_id, cycle_number, total_units_allowed=0, total_units_bought=0,
                 cycle_amount=0, cycle_status='active', start_date=None, end_date=None, id=None):
        """
        Initialize a new UserCycle instance
        
        Args:
            user_id (str or ObjectId): ID of the user
            cycle_number (int): The cycle number
            total_units_allowed (int, optional): Maximum units allowed in this cycle. Defaults to 0.
            total_units_bought (int, optional): Total units purchased by user. Defaults to 0.
            cycle_amount (Decimal or float, optional): Total amount spent in cycle. Defaults to 0.
            cycle_status (str, optional): Status of user's cycle participation. Defaults to 'active'.
            start_date (datetime, optional): Cycle start date. Defaults to None.
            end_date (datetime, optional): Cycle end date. Defaults to None.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.user_id = user_id
        self.cycle_number = cycle_number
        self.start_date = start_date
        self.end_date = end_date
        self.total_units_allowed = total_units_allowed
        self.total_units_bought = total_units_bought
        # Convert cycle_amount to Decimal for precision
        self.cycle_amount = Decimal(str(cycle_amount)) if not isinstance(cycle_amount, Decimal) else cycle_amount
        self.cycle_status = cycle_status
    
    def __repr__(self):
        return f"<UserCycle user_id={self.user_id} cycle={self.cycle_number} status={self.cycle_status}>"
    
    def to_dict(self):
        """
        Convert the UserCycle object to a dictionary
        
        Returns:
            dict: Dictionary representation of the UserCycle
        """
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "cycle_number": self.cycle_number,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_units_allowed": self.total_units_allowed,
            "total_units_bought": self.total_units_bought,
            "cycle_amount": float(self.cycle_amount) if isinstance(self.cycle_amount, Decimal) else self.cycle_amount,
            "cycle_status": self.cycle_status
        }
    
    def save(self):
        """
        Save the UserCycle object to the database
        
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
    def find_by_id(cls, cycle_id):
        """
        Find a UserCycle by ID
        
        Args:
            cycle_id (str or ObjectId): The ID of the UserCycle to find
            
        Returns:
            UserCycle or None: The found UserCycle object or None if not found
        """
        if isinstance(cycle_id, str):
            try:
                cycle_id = ObjectId(cycle_id)
            except:
                return None
            
        data = db[cls.COLLECTION].find_one({"_id": cycle_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user_and_cycle(cls, user_id, cycle_number):
        """
        Find a UserCycle by user ID and cycle number
        
        Args:
            user_id (str or ObjectId): The user ID
            cycle_number (int): The cycle number
            
        Returns:
            UserCycle or None: The found UserCycle object or None if not found
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass  # Keep as string if not a valid ObjectId
            
        data = db[cls.COLLECTION].find_one({
            "user_id": user_id,
            "cycle_number": cycle_number
        })
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user(cls, user_id, sort_by="cycle_number", sort_direction=-1, limit=None):
        """
        Find UserCycles for a specific user
        
        Args:
            user_id (str or ObjectId): The user ID
            sort_by (str, optional): Field to sort by. Defaults to "cycle_number".
            sort_direction (int, optional): Sort direction (1 for ascending, -1 for descending). Defaults to -1.
            limit (int, optional): Maximum number of records to return. Defaults to None.
            
        Returns:
            list: List of UserCycle objects for the user
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass  # Keep as string if not a valid ObjectId
            
        cursor = db[cls.COLLECTION].find({"user_id": user_id}).sort(sort_by, sort_direction)
        
        if limit:
            cursor = cursor.limit(limit)
            
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a UserCycle object from a dictionary
        
        Args:
            data (dict): Dictionary representing a UserCycle document
            
        Returns:
            UserCycle: A UserCycle object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            cycle_number=data.get("cycle_number"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            total_units_allowed=data.get("total_units_allowed", 0),
            total_units_bought=data.get("total_units_bought", 0),
            cycle_amount=data.get("cycle_amount", 0),
            cycle_status=data.get("cycle_status", "active")
        )
    
    @classmethod
    def get_all(cls, sort_by="cycle_number", sort_direction=-1):
        """
        Get all user cycles
        
        Args:
            sort_by (str, optional): Field to sort by. Defaults to "cycle_number".
            sort_direction (int, optional): Sort direction (1 for ascending, -1 for descending). Defaults to -1.
            
        Returns:
            list: List of UserCycle objects
        """
        cursor = db[cls.COLLECTION].find().sort(sort_by, sort_direction)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the UserCycle collection
        """
        # Compound index for fast user+cycle lookups
        db[cls.COLLECTION].create_index([("user_id", 1), ("cycle_number", 1)], unique=True)
        # Index for finding all cycles for a user
        db[cls.COLLECTION].create_index("user_id")