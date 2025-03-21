# app/services/system_service.py
import logging
from app import db
from datetime import datetime

logger = logging.getLogger('awardloop')

def get_system_setting(setting_key, default_value=None):
    """
    Retrieve a system setting from the database.
    
    Args:
        setting_key (str): The key of the setting to retrieve
        default_value: The default value to return if the setting is not found
        
    Returns:
        The setting value, or the default value if not found
    """
    try:
        setting = db.system_settings.find_one({"setting_key": setting_key})
        if setting:
            return setting["setting_value"]
        else:
            logger.debug(f"System setting '{setting_key}' not found, using default: {default_value}")
            return default_value
    except Exception as e:
        logger.error(f"Error retrieving system setting '{setting_key}': {e}")
        return default_value

def update_system_setting(setting_key, setting_value, description=None):
    """
    Update or create a system setting in the database.
    
    Args:
        setting_key (str): The key of the setting to update
        setting_value (str): The new value for the setting
        description (str, optional): A description of the setting
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare the update data
        update_data = {
            "setting_value": str(setting_value),
            "updated_at": datetime.utcnow()
        }
        
        # Add description if provided
        if description:
            update_data["setting_description"] = description
        
        # Try to update an existing setting
        result = db.system_settings.update_one(
            {"setting_key": setting_key},
            {"$set": update_data},
            upsert=False
        )
        
        # If no existing setting was updated, insert a new one
        if result.matched_count == 0:
            db.system_settings.insert_one({
                "setting_key": setting_key,
                "setting_value": str(setting_value),
                "setting_description": description if description else f"System setting for {setting_key}",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        
        logger.info(f"System setting '{setting_key}' updated to '{setting_value}'")
        return True
    except Exception as e:
        logger.error(f"Error updating system setting '{setting_key}': {e}")
        return False

def get_all_settings():
    """
    Retrieve all system settings.
    
    Returns:
        dict: Dictionary of all settings with key-value pairs
    """
    try:
        settings = list(db.system_settings.find({}))
        return {setting["setting_key"]: setting["setting_value"] for setting in settings}
    except Exception as e:
        logger.error(f"Error retrieving all system settings: {e}")
        return {}