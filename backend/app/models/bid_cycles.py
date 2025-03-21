# app/models/bid_cycles.py
from app import db
from datetime import datetime
from bson import ObjectId

class BidCycle:
    """
    BidCycle model for MongoDB
    
    Represents a bidding cycle in the system
    """
    
    COLLECTION = 'bid_cycles'
    
    def __init__(self, cycle_date, total_bids_allowed, bids_filled=0, 
                 cycle_status='pending', open_time=None, close_time=None,
                 created_at=None, updated_at=None, id=None,
                 next_cycle_trigger=None, cycle_conditions=None):
        """
        Initialize a new BidCycle instance
        
        Args:
            cycle_date (datetime.datetime): The date of the cycle (must be datetime object for MongoDB compatibility)
            total_bids_allowed (int): Maximum number of bids allowed in this cycle
            bids_filled (int, optional): Current number of bids filled. Defaults to 0.
            cycle_status (str, optional): Status of the cycle ('pending', 'open', 'closed'). Defaults to 'pending'.
            open_time (datetime, optional): Time when the cycle opens. Defaults to None.
            close_time (datetime, optional): Time when the cycle closes. Defaults to None.
            created_at (datetime, optional): Creation timestamp. Defaults to current UTC time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current UTC time.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
            next_cycle_trigger (dict, optional): Configuration for next cycle trigger. Defaults to None.
                Format: {
                    "only_open_when_filled": bool,
                    "open_time": str (format: "HH:MM:SS"),
                    "timezone": str (timezone name)
                }
            cycle_conditions (dict, optional): Conditions for cycle behavior. Defaults to None.
                Format: {
                    "auto_close_when_filled": bool,
                    "profit_distribution_day": float
                }
        """
        self.id = id
        self.cycle_date = cycle_date
        self.total_bids_allowed = total_bids_allowed
        self.bids_filled = bids_filled
        self.cycle_status = cycle_status
        self.open_time = open_time
        self.close_time = close_time
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # Set default values for new fields if not provided
        if next_cycle_trigger is None:
            self.next_cycle_trigger = {
                "only_open_when_filled": True,
                "open_time": "00:10:00",
                "timezone": "Asia/Kolkata"
            }
        else:
            self.next_cycle_trigger = next_cycle_trigger
            
        if cycle_conditions is None:
            self.cycle_conditions = {
                "auto_close_when_filled": True,
                "profit_distribution_day": 0.006
            }
        else:
            self.cycle_conditions = cycle_conditions
    def __repr__(self):
        return f"<BidCycle {self.id} - {self.cycle_date} - {self.cycle_status}>"
    
    def to_dict(self):
        """
        Convert the BidCycle object to a dictionary
        
        Returns:
            dict: Dictionary representation of the BidCycle
        """
        data = {
            "_id": self.id,
            "cycle_date": self.cycle_date,
            "total_bids_allowed": self.total_bids_allowed,
            "bids_filled": self.bids_filled,
            "cycle_status": self.cycle_status,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "next_cycle_trigger": self.next_cycle_trigger,
            "cycle_conditions": self.cycle_conditions
        }
        return data
    
    def save(self):
        """
        Save the BidCycle object to the database
        
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
    def find_by_id(cls, bid_cycle_id):
        """
        Find a BidCycle by ID
        
        Args:
            bid_cycle_id (str or ObjectId): The ID of the BidCycle to find
            
        Returns:
            BidCycle or None: The found BidCycle object or None if not found
        """
        if isinstance(bid_cycle_id, str):
            bid_cycle_id = ObjectId(bid_cycle_id)
            
        data = db[cls.COLLECTION].find_one({"_id": bid_cycle_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_all(cls):
        """
        Find all BidCycles
        
        Returns:
            list: List of BidCycle objects
        """
        cursor = db[cls.COLLECTION].find().sort("cycle_date", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_status(cls, status):
        """
        Find BidCycles by status
        
        Args:
            status (str): The status to filter by ('pending', 'open', 'closed')
            
        Returns:
            list: List of BidCycle objects with matching status
        """
        cursor = db[cls.COLLECTION].find({"cycle_status": status}).sort("cycle_date", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_current_open_cycle(cls):
        """
        Find the currently open bid cycle
        
        Returns:
            BidCycle or None: The currently open BidCycle or None if not found
        """
        data = db[cls.COLLECTION].find_one({"cycle_status": "open"})
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a BidCycle object from a dictionary
        
        Args:
            data (dict): Dictionary representing a BidCycle document
            
        Returns:
            BidCycle: A BidCycle object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            cycle_date=data.get("cycle_date"),
            total_bids_allowed=data.get("total_bids_allowed"),
            bids_filled=data.get("bids_filled", 0),
            cycle_status=data.get("cycle_status", "pending"),
            open_time=data.get("open_time"),
            close_time=data.get("close_time"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            next_cycle_trigger=data.get("next_cycle_trigger"),
            cycle_conditions=data.get("cycle_conditions")
        )
    
    @classmethod
    def get_investments(cls, bid_cycle_id):
        """
        Get investments associated with this BidCycle
        
        Args:
            bid_cycle_id (str or ObjectId): ID of the BidCycle
            
        Returns:
            list: List of investment documents
        """
        if isinstance(bid_cycle_id, str):
            bid_cycle_id = ObjectId(bid_cycle_id)
            
        # Query user_investments collection for documents referencing this cycle
        cursor = db.user_investments.find({"bid_cycle_id": bid_cycle_id})
        return list(cursor)
    
    @classmethod
    def delete_by_id(cls, bid_cycle_id):
        """
        Delete a BidCycle by ID
        
        Args:
            bid_cycle_id (str or ObjectId): ID of the BidCycle to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(bid_cycle_id, str):
            bid_cycle_id = ObjectId(bid_cycle_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": bid_cycle_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the BidCycle collection
        """
        db[cls.COLLECTION].create_index("cycle_date")
        db[cls.COLLECTION].create_index("cycle_status")
        db[cls.COLLECTION].create_index([("cycle_status", 1), ("cycle_date", -1)])