# app/models/unit_progression.py
from app import db
from bson import ObjectId

class UnitProgression:
    """
    UnitProgression model for MongoDB
    
    Defines how many units are allowed for each bid cycle number
    """
    
    COLLECTION = 'unit_progression'
    
    def __init__(self, cycle_number, units_allowed, id=None):
        """
        Initialize a new UnitProgression instance
        
        Args:
            cycle_number (int): The cycle number
            units_allowed (int): Number of units allowed for this cycle
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.cycle_number = cycle_number
        self.units_allowed = units_allowed
    
    def __repr__(self):
        return f"<UnitProgression cycle={self.cycle_number}, units={self.units_allowed}>"
    
    def to_dict(self):
        """
        Convert the UnitProgression object to a dictionary
        
        Returns:
            dict: Dictionary representation of the UnitProgression
        """
        return {
            "_id": self.id,
            "cycle_number": self.cycle_number,
            "units_allowed": self.units_allowed
        }
    
    def save(self):
        """
        Save the UnitProgression object to the database
        
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
    def find_by_id(cls, progression_id):
        """
        Find a UnitProgression by ID
        
        Args:
            progression_id (str or ObjectId): The ID of the UnitProgression to find
            
        Returns:
            UnitProgression or None: The found UnitProgression object or None if not found
        """
        if isinstance(progression_id, str):
            progression_id = ObjectId(progression_id)
            
        data = db[cls.COLLECTION].find_one({"_id": progression_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_cycle_number(cls, cycle_number):
        """
        Find a UnitProgression by cycle number
        
        Args:
            cycle_number (int): The cycle number to look up
            
        Returns:
            UnitProgression or None: The found UnitProgression object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"cycle_number": cycle_number})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a UnitProgression object from a dictionary
        
        Args:
            data (dict): Dictionary representing a UnitProgression document
            
        Returns:
            UnitProgression: A UnitProgression object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            cycle_number=data.get("cycle_number"),
            units_allowed=data.get("units_allowed")
        )
    
    @classmethod
    def get_all(cls):
        """
        Get all unit progression records
        
        Returns:
            list: List of UnitProgression objects
        """
        cursor = db[cls.COLLECTION].find().sort("cycle_number", 1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def delete_by_id(cls, progression_id):
        """
        Delete a UnitProgression by ID
        
        Args:
            progression_id (str or ObjectId): ID of the UnitProgression to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(progression_id, str):
            progression_id = ObjectId(progression_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": progression_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the UnitProgression collection
        """
        # Unique index on cycle_number for fast lookups
        db[cls.COLLECTION].create_index("cycle_number", unique=True)