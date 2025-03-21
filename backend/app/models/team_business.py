# app/models/team_business.py
"""
Model for tracking team business volume and rank levels.
Uses MongoDB directly instead of SQLAlchemy.
"""

from app import db
from datetime import datetime
from bson.objectid import ObjectId

class TeamBusiness:
    """MongoDB model for team business volume and rank tracking"""
    COLLECTION = 'team_business'
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """Get team business data for a specific user"""
        return db[cls.COLLECTION].find_one({"user_id": user_id})
    
    @classmethod
    def update_business_volume(cls, user_id, additional_volume):
        """
        Update a user's business volume and check for rank progression
        Returns the new business volume and rank level if updated
        """
        from app.models.team_rewards import TeamReward
        
        # Find existing team business record
        team_business = cls.find_by_user_id(user_id)
        
        if not team_business:
            # Create new team business record if it doesn't exist
            new_record = {
                "user_id": user_id,
                "business_volume": float(additional_volume),
                "current_rank_level": 1,  # Start at rank 1
                "created_at": datetime.utcnow(),
                "last_calculated_at": datetime.utcnow()
            }
            db[cls.COLLECTION].insert_one(new_record)
            return {"business_volume": float(additional_volume), "rank_level": 1, "is_new": True}
        
        # Update existing team business record with new volume
        current_volume = float(team_business.get("business_volume", 0))
        new_volume = current_volume + float(additional_volume)
        current_rank = team_business.get("current_rank_level", 1)
        
        # Check if user qualifies for a higher rank
        next_rank = TeamReward.find_next_rank(current_rank, new_volume)
        new_rank = current_rank
        
        if next_rank:
            # User has reached a new rank level
            new_rank = next_rank.get("rankLevel")
        
        # Update the record
        update_result = db[cls.COLLECTION].update_one(
            {"user_id": user_id},
            {"$set": {
                "business_volume": new_volume,
                "current_rank_level": new_rank,
                "last_calculated_at": datetime.utcnow()
            }}
        )
        
        rank_changed = new_rank > current_rank
        
        return {
            "business_volume": new_volume,
            "rank_level": new_rank,
            "previous_rank": current_rank,
            "rank_changed": rank_changed,
            "is_new": False
        }
    
    @classmethod
    def get_all_with_minimum_volume(cls, min_volume):
        """Get all users with a minimum business volume"""
        return list(db[cls.COLLECTION].find(
            {"business_volume": {"$gte": float(min_volume)}}
        ).sort("business_volume", -1))
    
    @classmethod
    def get_all_with_rank(cls, rank_level):
        """Get all users with a specific rank level"""
        return list(db[cls.COLLECTION].find(
            {"current_rank_level": rank_level}
        ).sort("business_volume", -1))
    
    @classmethod
    def get_all_users_with_ranks(cls):
        """Get all users with their current ranks and business volumes"""
        return list(db[cls.COLLECTION].find({}).sort("business_volume", -1))