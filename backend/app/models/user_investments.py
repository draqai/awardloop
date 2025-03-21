# app/models/user_investments.py
from app import db
from datetime import datetime
from bson import ObjectId, Decimal128
from decimal import Decimal

class UserInvestment:
    """
    UserInvestment model for MongoDB
    
    Represents a user's investment in the system
    """
    
    COLLECTION = 'user_investments'
    
    def __init__(self, user_id, amount, payment_hash=None, investment_status='pending',
                 bid_position=1, bid_cycle_id=None, bid_order=None, activation_date=None,
                 completion_date=None, created_at=None, id=None):
        """
        Initialize a new UserInvestment instance
        
        Args:
            user_id (int or ObjectId): The ID of the user making the investment
            amount (Decimal or float): The investment amount
            payment_hash (str, optional): Transaction hash for the payment. Defaults to None.
            investment_status (str, optional): Status of the investment ('pending', 'active', 'completed', 'blocked'). Defaults to 'pending'.
            bid_position (int, optional): Position in the bidding queue. Defaults to 1.
            bid_cycle_id (int or ObjectId, optional): Reference to BidCycle. Defaults to None.
            bid_order (int, optional): Order in the bidding process. Defaults to None.
            activation_date (datetime, optional): Date when investment was activated. Defaults to None.
            completion_date (datetime, optional): Date when investment was completed. Defaults to None.
            created_at (datetime, optional): Creation timestamp. Defaults to current UTC time.
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
            
        self.payment_hash = payment_hash
        self.investment_status = investment_status
        self.bid_position = bid_position
        self.bid_cycle_id = bid_cycle_id
        self.bid_order = bid_order
        self.activation_date = activation_date
        self.completion_date = completion_date
        self.created_at = created_at or datetime.utcnow()
    
    def __repr__(self):
        return f"<UserInvestment id={self.id}, user_id={self.user_id}, amount={self.amount}>"
    
    def to_dict(self):
        """
        Convert the UserInvestment object to a dictionary
        
        Returns:
            dict: Dictionary representation of the UserInvestment
        """
        # Convert Decimal to Decimal128 for MongoDB storage
        amount = Decimal128(self.amount) if isinstance(self.amount, Decimal) else Decimal128(Decimal(str(self.amount)))
        
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "amount": amount,
            "payment_hash": self.payment_hash,
            "investment_status": self.investment_status,
            "bid_position": self.bid_position,
            "bid_cycle_id": self.bid_cycle_id,
            "bid_order": self.bid_order,
            "activation_date": self.activation_date,
            "completion_date": self.completion_date,
            "created_at": self.created_at
        }
    
    def save(self):
        """
        Save the UserInvestment object to the database
        
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
    def find_by_id(cls, investment_id):
        """
        Find a UserInvestment by ID
        
        Args:
            investment_id (str or ObjectId): The ID of the UserInvestment to find
            
        Returns:
            UserInvestment or None: The found UserInvestment object or None if not found
        """
        if isinstance(investment_id, str):
            investment_id = ObjectId(investment_id)
            
        data = db[cls.COLLECTION].find_one({"_id": investment_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """
        Find all investments by a specific user
        
        Args:
            user_id (int or ObjectId): The ID of the user
            
        Returns:
            list: List of UserInvestment objects for the user
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        cursor = db[cls.COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_bid_cycle_id(cls, bid_cycle_id):
        """
        Find all investments in a specific bid cycle
        
        Args:
            bid_cycle_id (int or ObjectId): The ID of the BidCycle
            
        Returns:
            list: List of UserInvestment objects in the bid cycle
        """
        if isinstance(bid_cycle_id, str):
            try:
                bid_cycle_id = ObjectId(bid_cycle_id)
            except:
                pass
                
        cursor = db[cls.COLLECTION].find({"bid_cycle_id": bid_cycle_id}).sort("bid_order", 1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_status(cls, status):
        """
        Find all investments with a specific status
        
        Args:
            status (str): The investment status to filter by
            
        Returns:
            list: List of UserInvestment objects with the status
        """
        cursor = db[cls.COLLECTION].find({"investment_status": status}).sort("created_at", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a UserInvestment object from a dictionary
        
        Args:
            data (dict): Dictionary representing a UserInvestment document
            
        Returns:
            UserInvestment: A UserInvestment object created from the dictionary
        """
        # Convert Decimal128 back to Decimal
        amount = data.get("amount")
        if isinstance(amount, Decimal128):
            amount = amount.to_decimal()
            
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            amount=amount,
            payment_hash=data.get("payment_hash"),
            investment_status=data.get("investment_status", "pending"),
            bid_position=data.get("bid_position", 1),
            bid_cycle_id=data.get("bid_cycle_id"),
            bid_order=data.get("bid_order"),
            activation_date=data.get("activation_date"),
            completion_date=data.get("completion_date"),
            created_at=data.get("created_at")
        )
    
    @classmethod
    def count_by_status(cls, status):
        """
        Count investments with a specific status
        
        Args:
            status (str): The investment status to count
            
        Returns:
            int: The count of investments with the status
        """
        return db[cls.COLLECTION].count_documents({"investment_status": status})
    
    @classmethod
    def get_user(cls, investment_id):
        """
        Get the user associated with this investment
        
        Args:
            investment_id (str or ObjectId): ID of the UserInvestment
            
        Returns:
            User or None: The associated User object or None
        """
        from app.models.user import User
        
        investment = cls.find_by_id(investment_id)
        if not investment:
            return None
            
        return User.find_by_id(investment.user_id)
    
    @classmethod
    def get_bid_cycle(cls, investment_id):
        """
        Get the bid cycle associated with this investment
        
        Args:
            investment_id (str or ObjectId): ID of the UserInvestment
            
        Returns:
            BidCycle or None: The associated BidCycle object or None
        """
        from app.models.bid_cycles import BidCycle
        
        investment = cls.find_by_id(investment_id)
        if not investment or not investment.bid_cycle_id:
            return None
            
        return BidCycle.find_by_id(investment.bid_cycle_id)
    
    @classmethod
    def delete_by_id(cls, investment_id):
        """
        Delete a UserInvestment by ID
        
        Args:
            investment_id (str or ObjectId): ID of the UserInvestment to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(investment_id, str):
            investment_id = ObjectId(investment_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": investment_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the UserInvestment collection
        """
        db[cls.COLLECTION].create_index("user_id")
        db[cls.COLLECTION].create_index("bid_cycle_id")
        db[cls.COLLECTION].create_index("investment_status")
        db[cls.COLLECTION].create_index([("investment_status", 1), ("created_at", -1)])
        db[cls.COLLECTION].create_index([("bid_cycle_id", 1), ("bid_order", 1)])