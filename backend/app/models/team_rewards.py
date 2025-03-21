# app/models/team_rewards.py
"""
Model for team rewards based on rank level and business volume.
Rewards are given when a user reaches specific business volume thresholds.
This model uses MongoDB directly.
"""

from app import db
from datetime import datetime
from bson.objectid import ObjectId

class TeamReward:
    """
    MongoDB model for team rewards based on rank level and business volume.
    """
    COLLECTION = 'team_rewards'
    
    @classmethod
    def find_all(cls):
        """Get all team rewards"""
        return list(db[cls.COLLECTION].find({"isActive": True}).sort("rankLevel", 1))
    
    @classmethod
    def find_by_rank(cls, rank_level):
        """Get team reward by rank level"""
        return db[cls.COLLECTION].find_one({"rankLevel": rank_level, "isActive": True})
    
    @classmethod
    def find_next_rank(cls, current_rank, business_volume):
        """Find the next rank level based on business volume"""
        return db[cls.COLLECTION].find_one({
            "rankLevel": {"$gt": current_rank},
            "businessVolume": {"$lte": business_volume},
            "isActive": True
        }, sort=[("rankLevel", 1)])
    
    @classmethod
    def create(cls, rank_level, business_volume, reward_amount, is_active=True):
        """Create a new team reward level"""
        reward_data = {
            "rankLevel": rank_level,
            "businessVolume": business_volume,
            "rewardAmount": reward_amount,
            "isActive": is_active,
            "createdAt": datetime.utcnow()
        }
        result = db[cls.COLLECTION].insert_one(reward_data)
        return result.inserted_id
    
    @classmethod
    def update(cls, rank_level, business_volume=None, reward_amount=None, is_active=None):
        """Update an existing team reward level"""
        update_data = {}
        if business_volume is not None:
            update_data["businessVolume"] = business_volume
        if reward_amount is not None:
            update_data["rewardAmount"] = reward_amount
        if is_active is not None:
            update_data["isActive"] = is_active
        
        if update_data:
            update_data["updatedAt"] = datetime.utcnow()
            result = db[cls.COLLECTION].update_one(
                {"rankLevel": rank_level},
                {"$set": update_data}
            )
            return result.modified_count > 0
        return False
    
    @classmethod
    def delete(cls, rank_level):
        """Delete a team reward level"""
        result = db[cls.COLLECTION].delete_one({"rankLevel": rank_level})
        return result.deleted_count > 0
    
    @classmethod
    def init_default_rewards(cls):
        """Initialize default team rewards if collection is empty"""
        if db[cls.COLLECTION].count_documents({}) == 0:
            default_rewards = [
                {
                    "_id": 1,
                    "rankLevel": 1,
                    "businessVolume": 2000,
                    "rewardAmount": 16.00,
                    "isActive": True
                },
                {
                    "_id": 2,
                    "rankLevel": 2,
                    "businessVolume": 10000,
                    "rewardAmount": 85.00,
                    "isActive": True
                },
                {
                    "_id": 3,
                    "rankLevel": 3,
                    "businessVolume": 25000,
                    "rewardAmount": 60.00,
                    "isActive": True
                },
                {
                    "_id": 4,
                    "rankLevel": 4,
                    "businessVolume": 75000,
                    "rewardAmount": 100.00,
                    "isActive": True
                },
                {
                    "_id": 5,
                    "rankLevel": 5,
                    "businessVolume": 300000,
                    "rewardAmount": 300.00,
                    "isActive": True
                },
                {
                    "_id": 6,
                    "rankLevel": 6,
                    "businessVolume": 1000000,
                    "rewardAmount": 1000.00,
                    "isActive": True
                },
                {
                    "_id": 7,
                    "rankLevel": 7,
                    "businessVolume": 4000000,
                    "rewardAmount": 4000.00,
                    "isActive": True
                },
                {
                    "_id": 8,
                    "rankLevel": 8,
                    "businessVolume": 15000000,
                    "rewardAmount": 15000.00,
                    "isActive": True
                },
                {
                    "_id": 9,
                    "rankLevel": 9,
                    "businessVolume": 75000000,
                    "rewardAmount": 75000.00,
                    "isActive": True
                },
                {
                    "_id": 10,
                    "rankLevel": 10,
                    "businessVolume": 250000000,
                    "rewardAmount": 250000.00,
                    "isActive": True
                },
                {
                    "_id": 11,
                    "rankLevel": 11,
                    "businessVolume": 1000000000,
                    "rewardAmount": 1000000.00,
                    "isActive": True
                },
                {
                    "_id": 12,
                    "rankLevel": 12,
                    "businessVolume": 2147483647,
                    "rewardAmount": 1500000.00,
                    "isActive": True
                }
            ]
            db[cls.COLLECTION].insert_many(default_rewards)
            return True
        return False