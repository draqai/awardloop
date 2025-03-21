# app/models/user_earnings.py
from app import db
from datetime import datetime
from bson import ObjectId, Decimal128
from decimal import Decimal

class UserEarning:
    """
    UserEarning model for MongoDB
    
    Tracks earnings for users, including daily profits, referral commissions, and team rewards
    """
    
    COLLECTION = 'user_earnings'
    
    def __init__(self, user_id, amount, source_id=None, earning_type='daily', 
                 earning_level=None, earning_status='pending', created_at=None,
                 processed_at=None, id=None):
        """
        Initialize a new UserEarning instance
        
        Args:
            user_id (int or ObjectId): The ID of the user who earned
            amount (Decimal or float): The earned amount
            source_id (int or ObjectId, optional): ID reference to the source of earnings. Defaults to None.
            earning_type (str, optional): Type of earning ('daily', 'referral', 'team_reward'). Defaults to 'daily'.
            earning_level (int, optional): Level in referral structure (for referral earnings). Defaults to None.
            earning_status (str, optional): Status of the earning ('pending', 'processed', 'paid'). Defaults to 'pending'.
            created_at (datetime, optional): Creation timestamp. Defaults to current UTC time.
            processed_at (datetime, optional): When the earning was processed. Defaults to None.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.user_id = user_id
        
        # Convert amount to Decimal for proper handling
        if isinstance(amount, float) or isinstance(amount, int) or isinstance(amount, str):
            self.amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            self.amount = amount
        else:
            self.amount = Decimal('0.0')
            
        self.source_id = source_id
        self.earning_type = earning_type
        self.earning_level = earning_level
        self.earning_status = earning_status
        self.created_at = created_at or datetime.utcnow()
        self.processed_at = processed_at
    
    def __repr__(self):
        return f"<UserEarning user_id={self.user_id}, amount={self.amount}, type={self.earning_type}>"
    
    def to_dict(self):
        """
        Convert the UserEarning object to a dictionary
        
        Returns:
            dict: Dictionary representation of the UserEarning
        """
        # Convert Decimal to Decimal128 for MongoDB storage
        amount = Decimal128(self.amount) if isinstance(self.amount, Decimal) else Decimal128(Decimal(str(self.amount)))
        
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "source_id": self.source_id,
            "amount": amount,
            "earning_type": self.earning_type,
            "earning_level": self.earning_level,
            "earning_status": self.earning_status,
            "created_at": self.created_at,
            "processed_at": self.processed_at
        }
    
    def save(self):
        """
        Save the UserEarning object to the database
        
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
    def find_by_id(cls, earning_id):
        """
        Find a UserEarning by ID
        
        Args:
            earning_id (str or ObjectId): The ID of the UserEarning to find
            
        Returns:
            UserEarning or None: The found UserEarning object or None if not found
        """
        if isinstance(earning_id, str):
            earning_id = ObjectId(earning_id)
            
        data = db[cls.COLLECTION].find_one({"_id": earning_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user_id(cls, user_id, limit=None, skip=None, sort_by=None):
        """
        Find all earnings for a specific user
        
        Args:
            user_id (int or ObjectId): The ID of the user
            limit (int, optional): Maximum number of results to return. Defaults to None.
            skip (int, optional): Number of results to skip. Defaults to None.
            sort_by (tuple, optional): Field and direction to sort by, e.g. ('created_at', -1). Defaults to None.
            
        Returns:
            list: List of UserEarning objects for the user
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        query = {"user_id": user_id}
        cursor = db[cls.COLLECTION].find(query)
        
        # Apply sorting if provided
        if sort_by:
            field, direction = sort_by
            cursor = cursor.sort(field, direction)
        else:
            # Default sorting by created_at descending
            cursor = cursor.sort("created_at", -1)
        
        # Apply pagination if provided
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_type(cls, earning_type, status=None):
        """
        Find all earnings of a specific type
        
        Args:
            earning_type (str): The earning type to filter by
            status (str, optional): Filter by status as well. Defaults to None.
            
        Returns:
            list: List of UserEarning objects with the type
        """
        query = {"earning_type": earning_type}
        if status:
            query["earning_status"] = status
            
        cursor = db[cls.COLLECTION].find(query).sort("created_at", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_status(cls, status):
        """
        Find all earnings with a specific status
        
        Args:
            status (str): The earning status to filter by
            
        Returns:
            list: List of UserEarning objects with the status
        """
        cursor = db[cls.COLLECTION].find({"earning_status": status}).sort("created_at", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a UserEarning object from a dictionary
        
        Args:
            data (dict): Dictionary representing a UserEarning document
            
        Returns:
            UserEarning: A UserEarning object created from the dictionary
        """
        # Convert Decimal128 back to Decimal
        amount = data.get("amount")
        if isinstance(amount, Decimal128):
            amount = amount.to_decimal()
            
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            source_id=data.get("source_id"),
            amount=amount,
            earning_type=data.get("earning_type", "daily"),
            earning_level=data.get("earning_level"),
            earning_status=data.get("earning_status", "pending"),
            created_at=data.get("created_at"),
            processed_at=data.get("processed_at")
        )
    
    @classmethod
    def get_user(cls, earning_id):
        """
        Get the user associated with this earning
        
        Args:
            earning_id (str or ObjectId): ID of the UserEarning
            
        Returns:
            User or None: The associated User object or None
        """
        from app.models.user import User
        
        earning = cls.find_by_id(earning_id)
        if not earning:
            return None
            
        return User.find_by_id(earning.user_id)
    
    @classmethod
    def sum_by_user_and_type(cls, user_id, earning_type, status=None):
        """
        Sum earnings for a user by type and optionally status
        
        Args:
            user_id (int or ObjectId): The user ID
            earning_type (str): The earning type to sum
            status (str, optional): Filter by status. Defaults to None.
            
        Returns:
            Decimal: The total sum of earnings
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        match = {
            "user_id": user_id,
            "earning_type": earning_type
        }
        
        if status:
            match["earning_status"] = status
            
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }}
        ]
        
        result = list(db[cls.COLLECTION].aggregate(pipeline))
        
        if result and len(result) > 0:
            total = result[0].get("total")
            if isinstance(total, Decimal128):
                return total.to_decimal()
            return Decimal(str(total)) if total else Decimal("0")
        
        return Decimal("0")
    
    @classmethod
    def delete_by_id(cls, earning_id):
        """
        Delete a UserEarning by ID
        
        Args:
            earning_id (str or ObjectId): ID of the UserEarning to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(earning_id, str):
            earning_id = ObjectId(earning_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": earning_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the UserEarning collection
        """
        db[cls.COLLECTION].create_index("user_id")
        db[cls.COLLECTION].create_index("earning_type")
        db[cls.COLLECTION].create_index("earning_status")
        db[cls.COLLECTION].create_index([("user_id", 1), ("earning_type", 1)])
        db[cls.COLLECTION].create_index([("user_id", 1), ("earning_status", 1)])
        db[cls.COLLECTION].create_index([("earning_type", 1), ("earning_status", 1)])
        db[cls.COLLECTION].create_index([("user_id", 1), ("earning_type", 1), ("earning_status", 1)])
        db[cls.COLLECTION].create_index("created_at")