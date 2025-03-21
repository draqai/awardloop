# app/services/referral_service.py
from app import db
from app.models.referral_tree import ReferralTree
from app.models.user_earnings import UserEarning
from app.models.investment_plans import InvestmentPlan
from app.models.income_hold_status import IncomeHoldStatus
from datetime import datetime
from bson.objectid import ObjectId

class ReferralService:
    @staticmethod
    def get_upline(user_id, levels=12):
        """Get the upline for a user up to the specified number of levels"""
        upline = []
        current_id = user_id
        
        for level in range(1, levels + 1):
            # Find referrer using MongoDB model
            referrer_rel = ReferralTree.find_by_user_id(current_id)
            
            if not referrer_rel or not referrer_rel.referrer_id:
                break
                
            upline.append({
                'user_id': referrer_rel.referrer_id,
                'level': level
            })
            
            # Move up to the next level
            current_id = referrer_rel.referrer_id
        
        return upline
    
    @staticmethod
    def calculate_level_commission(investment_amount, level):
        """Calculate commission for a specific referral level"""
        # Get commission percentage for this level
        plan_data = db.investment_plans.find_one({'plan_level': level, 'is_active': True})
        
        if not plan_data:
            return 0
            
        # Calculate commission
        commission_percentage = float(plan_data.get('daily_percentage', 0))
        return investment_amount * (commission_percentage / 100)
    
    @staticmethod
    def distribute_commissions(user_id, investment_amount):
        """Distribute commissions to the referral upline"""
        # Get upline
        upline = ReferralService.get_upline(user_id)
        
        for level_data in upline:
            referrer_id = level_data['user_id']
            level = level_data['level']
            
            # Calculate commission for this level
            commission = ReferralService.calculate_level_commission(investment_amount, level)
            
            if commission <= 0:
                continue
                
            # Always mark earnings as pending - they will be distributed 
            # through the REWARDS_WALLET_ADDRESS after cycle closes
            earning_status = 'pending'
            
            # Create earning record with MongoDB
            earning_data = {
                'user_id': referrer_id,
                'source_id': user_id,
                'amount': commission,
                'earning_type': 'referral',
                'earning_level': level,
                'earning_status': earning_status,
                'created_at': datetime.utcnow()
            }
            
            if earning_status == 'processed':
                earning_data['processed_at'] = datetime.utcnow()
                
            db.user_earnings.insert_one(earning_data)
        
        return True
    
    @staticmethod
    def process_team_business_rewards(user_id, investment_amount):
        """
        Process team business rewards for users who qualify
        User must have 5 active legs with referrals who also maintain 5 active legs
        """
        # Get the required number of legs
        system_settings = db.system_settings.find_one({'key': 'min_legs_for_reward'})
        min_legs = int(system_settings.get('value', '5') if system_settings else 5)
        
        # Get all users with the required number of active legs
        qualified_users = db.user_legs.find({'active_legs': {'$gte': min_legs}})
        
        for qualified_user in qualified_users:
            qualified_user_id = qualified_user.get('user_id')
            
            # Update their business volume
            team_business = db.team_business.find_one({'user_id': qualified_user_id})
            
            if not team_business:
                # Create new team business record
                team_business_data = {
                    'user_id': qualified_user_id,
                    'business_volume': investment_amount,
                    'current_rank_level': 1,  # Start at rank 1
                    'created_at': datetime.utcnow(),
                    'last_calculated_at': datetime.utcnow()
                }
                db.team_business.insert_one(team_business_data)
            else:
                # Update existing team business record
                new_volume = team_business.get('business_volume', 0) + investment_amount
                db.team_business.update_one(
                    {'user_id': qualified_user_id},
                    {'$set': {
                        'business_volume': new_volume,
                        'last_calculated_at': datetime.utcnow()
                    }}
                )
                
                # Check if user qualifies for a higher rank
                current_rank = team_business.get('current_rank_level', 1)
                next_rank = db.team_rewards.find_one({
                    'rank_level': {'$gt': current_rank},
                    'business_volume': {'$lte': new_volume},
                    'is_active': True
                }, sort=[('rank_level', 1)])
                
                if next_rank:
                    # User has reached a new rank level
                    db.team_business.update_one(
                        {'user_id': qualified_user_id},
                        {'$set': {'current_rank_level': next_rank.get('rank_level')}}
                    )
                    
                    # Create earning record as pending - will be distributed 
                    # from REWARDS_WALLET_ADDRESS after cycle closes
                    earning_data = {
                        'user_id': qualified_user_id,
                        'amount': next_rank.get('reward_amount'),
                        'earning_type': 'team_reward',
                        'earning_level': next_rank.get('rank_level'),
                        'earning_status': 'pending',  # Always pending until cycle closes
                        'created_at': datetime.utcnow()
                    }
                    db.user_earnings.insert_one(earning_data)
        
        return True