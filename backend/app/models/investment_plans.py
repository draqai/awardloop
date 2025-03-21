# app/models/investment_plans.py
from app import db
from bson import ObjectId, Decimal128
from decimal import Decimal

class InvestmentPlan:
    """
    InvestmentPlan model for MongoDB
    
    Represents available investment plans in the system
    """
    
    COLLECTION = 'investment_plans'
    
    def __init__(self, plan_level, daily_percentage, plan_description=None, 
                 min_days=5, is_active=True, id=None):
        """
        Initialize a new InvestmentPlan instance
        
        Args:
            plan_level (int): The level of this investment plan
            daily_percentage (Decimal or float): Daily percentage return
            plan_description (str, optional): Description of the plan. Defaults to None.
            min_days (int, optional): Minimum days for investment. Defaults to 5.
            is_active (bool, optional): Whether this plan is active. Defaults to True.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.plan_level = plan_level
        
        # Convert daily_percentage to Decimal for proper handling
        if isinstance(daily_percentage, float) or isinstance(daily_percentage, int) or isinstance(daily_percentage, str):
            self.daily_percentage = Decimal(str(daily_percentage))
        elif isinstance(daily_percentage, Decimal):
            self.daily_percentage = daily_percentage
        else:
            self.daily_percentage = Decimal('0.0')
            
        self.plan_description = plan_description
        self.min_days = min_days
        self.is_active = is_active
    
    def __repr__(self):
        return f"<InvestmentPlan level={self.plan_level}, percentage={self.daily_percentage}>"
    
    def to_dict(self):
        """
        Convert the InvestmentPlan object to a dictionary
        
        Returns:
            dict: Dictionary representation of the InvestmentPlan
        """
        # Convert Decimal to Decimal128 for MongoDB storage
        daily_percentage = Decimal128(self.daily_percentage) if isinstance(self.daily_percentage, Decimal) else Decimal128(Decimal(str(self.daily_percentage)))
        
        return {
            "_id": self.id,
            "plan_level": self.plan_level,
            "daily_percentage": daily_percentage,
            "plan_description": self.plan_description,
            "min_days": self.min_days,
            "is_active": self.is_active
        }
    
    def save(self):
        """
        Save the InvestmentPlan object to the database
        
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
    def find_by_id(cls, plan_id):
        """
        Find an InvestmentPlan by ID
        
        Args:
            plan_id (str or ObjectId): The ID of the InvestmentPlan to find
            
        Returns:
            InvestmentPlan or None: The found InvestmentPlan object or None if not found
        """
        if isinstance(plan_id, str):
            plan_id = ObjectId(plan_id)
            
        data = db[cls.COLLECTION].find_one({"_id": plan_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_level(cls, plan_level):
        """
        Find an InvestmentPlan by plan level
        
        Args:
            plan_level (int): The plan level to look up
            
        Returns:
            InvestmentPlan or None: The found InvestmentPlan object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"plan_level": plan_level})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_active_plans(cls):
        """
        Find all active investment plans
        
        Returns:
            list: List of active InvestmentPlan objects
        """
        cursor = db[cls.COLLECTION].find({"is_active": True}).sort("plan_level", 1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create an InvestmentPlan object from a dictionary
        
        Args:
            data (dict): Dictionary representing an InvestmentPlan document
            
        Returns:
            InvestmentPlan: An InvestmentPlan object created from the dictionary
        """
        # Convert Decimal128 back to Decimal
        daily_percentage = data.get("daily_percentage")
        if isinstance(daily_percentage, Decimal128):
            daily_percentage = daily_percentage.to_decimal()
            
        return cls(
            id=data.get("_id"),
            plan_level=data.get("plan_level"),
            daily_percentage=daily_percentage,
            plan_description=data.get("plan_description"),
            min_days=data.get("min_days", 5),
            is_active=data.get("is_active", True)
        )
    
    @classmethod
    def get_all(cls):
        """
        Get all investment plans
        
        Returns:
            list: List of all InvestmentPlan objects
        """
        cursor = db[cls.COLLECTION].find().sort("plan_level", 1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def delete_by_id(cls, plan_id):
        """
        Delete an InvestmentPlan by ID
        
        Args:
            plan_id (str or ObjectId): ID of the InvestmentPlan to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(plan_id, str):
            plan_id = ObjectId(plan_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": plan_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the InvestmentPlan collection
        """
        db[cls.COLLECTION].create_index("plan_level", unique=True)
        db[cls.COLLECTION].create_index("is_active")