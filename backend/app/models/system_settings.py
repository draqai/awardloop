# app/models/system_settings.py
from app import db
from datetime import datetime
from bson import ObjectId

class SystemSettings:
    """
    SystemSettings model for MongoDB
    
    Provides key-value storage for system configuration settings
    """
    
    COLLECTION = 'system_settings'
    
    def __init__(self, setting_key, setting_value, setting_description=None, 
                 updated_at=None, id=None):
        """
        Initialize a new SystemSettings instance
        
        Args:
            setting_key (str): The unique key for this setting
            setting_value (str): The value of the setting
            setting_description (str, optional): Description of the setting. Defaults to None.
            updated_at (datetime, optional): Last update timestamp. Defaults to current UTC time.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.setting_key = setting_key
        self.setting_value = setting_value
        self.setting_description = setting_description
        self.updated_at = updated_at or datetime.utcnow()
    
    def __repr__(self):
        return f"<SystemSetting {self.setting_key}={self.setting_value}>"
    
    def to_dict(self):
        """
        Convert the SystemSettings object to a dictionary
        
        Returns:
            dict: Dictionary representation of the SystemSettings
        """
        return {
            "_id": self.id,
            "setting_key": self.setting_key,
            "setting_value": self.setting_value,
            "setting_description": self.setting_description,
            "updated_at": self.updated_at
        }
    
    def save(self):
        """
        Save the SystemSettings object to the database
        
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
    def find_by_id(cls, setting_id):
        """
        Find a SystemSettings by ID
        
        Args:
            setting_id (str or ObjectId): The ID of the SystemSettings to find
            
        Returns:
            SystemSettings or None: The found SystemSettings object or None if not found
        """
        if isinstance(setting_id, str):
            setting_id = ObjectId(setting_id)
            
        data = db[cls.COLLECTION].find_one({"_id": setting_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_key(cls, key):
        """
        Find a SystemSettings by key
        
        Args:
            key (str): The setting key to look up
            
        Returns:
            SystemSettings or None: The found SystemSettings object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"setting_key": key})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a SystemSettings object from a dictionary
        
        Args:
            data (dict): Dictionary representing a SystemSettings document
            
        Returns:
            SystemSettings: A SystemSettings object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            setting_key=data.get("setting_key"),
            setting_value=data.get("setting_value"),
            setting_description=data.get("setting_description"),
            updated_at=data.get("updated_at")
        )
    
    @staticmethod
    def get_value(key, default=None):
        """
        Get a setting value by key with optional default
        
        Args:
            key (str): The setting key to look up
            default (any, optional): Default value if setting not found. Defaults to None.
            
        Returns:
            str: The setting value or default if not found
        """
        data = db[SystemSettings.COLLECTION].find_one({"setting_key": key})
        
        if data:
            return data.get("setting_value")
        return default
    
    @staticmethod
    def set_value(key, value, description=None):
        """
        Set a setting value, create if not exists
        
        Args:
            key (str): The setting key
            value (str): The setting value
            description (str, optional): Description of the setting. Defaults to None.
            
        Returns:
            dict: The updated or created document
        """
        updated_at = datetime.utcnow()
        
        # Update or insert (upsert) the setting
        result = db[SystemSettings.COLLECTION].update_one(
            {"setting_key": key},
            {
                "$set": {
                    "setting_value": value,
                    "setting_description": description,
                    "updated_at": updated_at
                }
            },
            upsert=True
        )
        
        # Retrieve and return the updated or created setting
        return db[SystemSettings.COLLECTION].find_one({"setting_key": key})
    
    @classmethod
    def get_all(cls):
        """
        Get all system settings
        
        Returns:
            list: List of SystemSettings objects
        """
        cursor = db[cls.COLLECTION].find()
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def delete_by_key(cls, key):
        """
        Delete a setting by key
        
        Args:
            key (str): The setting key to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        result = db[cls.COLLECTION].delete_one({"setting_key": key})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the SystemSettings collection
        """
        # Unique index on setting_key for fast lookups
        db[cls.COLLECTION].create_index("setting_key", unique=True)