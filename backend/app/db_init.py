"""
MongoDB Initialization Script

This script initializes the MongoDB database with required indexes
and default collections for the application.
Previously, this application used SQLAlchemy with MySQL, but it has been
fully migrated to MongoDB.
"""

from app import get_db
from pymongo.errors import OperationFailure, ConnectionFailure
from datetime import datetime

def init_mongodb():
    """Initialize MongoDB with necessary indexes and default data"""
    try:
        # Get MongoDB database instance
        db = get_db()
        
        # Check if db is None (not if it's falsey)
        if db is None:
            print("ERROR: Could not connect to MongoDB database.")
            return False
            
        print("Initializing MongoDB database...")
        print("Note: This application has been migrated from SQLAlchemy/MySQL to MongoDB")
        
        # Create indexes for users collection
        print("Creating indexes for users collection...")
        db.users.create_index('sponsor_id', unique=True)
        db.users.create_index('email', unique=True)
        db.users.create_index('wallet_address', unique=True)
        
        # Create indexes for referral_tree collection
        print("Creating indexes for referral_tree collection...")
        db.referral_tree.create_index('user_id', unique=True)
        db.referral_tree.create_index('referrer_id')
        
        # Create indexes for user investments
        print("Creating indexes for user_investments collection...")
        db.user_investments.create_index([('user_id', 1), ('status', 1)])
        
        # Create indexes for user earnings
        print("Creating indexes for user_earnings collection...")
        db.user_earnings.create_index([('user_id', 1), ('earning_type', 1), ('earning_status', 1)])
        db.user_earnings.create_index([('user_id', 1), ('earning_status', 1)])
        db.user_earnings.create_index('created_at')
        
        # Create indexes for team business
        print("Creating indexes for team_business collection...")
        db.team_business.create_index('user_id', unique=True)
        
        # Create indexes for user legs
        print("Creating indexes for user_legs collection...")
        db.user_legs.create_index('user_id', unique=True)
        
        # Create system settings if not exists
        print("Setting up system settings...")
        if db.system_settings.count_documents({}) == 0:
            default_settings = [
                {'setting_key': 'min_legs_for_reward', 'setting_value': '5', 'setting_description': 'Minimum number of active legs required for team rewards'},
                {'setting_key': 'referral_bonus_percentage', 'setting_value': '5', 'setting_description': 'Percentage bonus for direct referrals'},
                {'setting_key': 'bid_timezone', 'setting_value': 'Asia/Kolkata', 'setting_description': 'Timezone for bid cycle operations'},
                {'setting_key': 'bid_open_time', 'setting_value': '08:00:00', 'setting_description': 'Time when bid cycles open'},
                {'setting_key': 'bid_cycle_status', 'setting_value': 'pending', 'setting_description': 'Current status of bid cycle'},
            ]
            db.system_settings.insert_many(default_settings)
            print("Default system settings created.")
        else:
            print("System settings already exist.")
            
        # Create indexes for all MongoDB models
        from app.models.user import User
        from app.models.referral_tree import ReferralTree
        from app.models.bid_cycles import BidCycle
        from app.models.user_investments import UserInvestment
        from app.models.system_settings import SystemSettings
        from app.models.unit_progression import UnitProgression
        from app.models.user_earnings import UserEarning
        from app.models.investment_plans import InvestmentPlan
        from app.models.income_hold_status import IncomeHoldStatus
        from app.models.user_wallet import UserWallet
        from app.models.pending_transaction import PendingTransaction
        from app.models.transaction import TatumTransaction
        
        print("Creating indexes for all MongoDB models...")
        User.ensure_indexes()
        ReferralTree.ensure_indexes()
        BidCycle.ensure_indexes()
        UserInvestment.ensure_indexes()
        SystemSettings.ensure_indexes()
        UnitProgression.ensure_indexes()
        UserEarning.ensure_indexes()
        InvestmentPlan.ensure_indexes()
        IncomeHoldStatus.ensure_indexes()
        UserWallet.ensure_indexes()
        PendingTransaction.ensure_indexes()
        TatumTransaction.ensure_indexes()
        
        # Add indexes for UserCycle model
        from app.models.user_cycles import UserCycle
        UserCycle.ensure_indexes()
        
        # Add indexes for SystemLog model
        try:
            db.system_log.create_index("log_type")
            db.system_log.create_index("created_at")
            print("SystemLog indexes created successfully.")
        except Exception as e:
            print(f"Warning: Could not create system_log indexes: {str(e)}")
        
        print("MongoDB initialization complete!")
        return True
        
    except ConnectionFailure as e:
        print(f"ERROR: Could not connect to MongoDB server: {str(e)}")
        return False
    except OperationFailure as e:
        print(f"ERROR: MongoDB operation failed: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: MongoDB initialization failed: {str(e)}")
        return False

def create_admin_user_if_not_exists():
    """Create an admin user if one doesn't exist yet"""
    try:
        # Get MongoDB database instance
        db = get_db()
        if db is None:
            print("ERROR: Could not connect to MongoDB database to create admin user.")
            return False
            
        from app.models.user import User
        from werkzeug.security import generate_password_hash
        
        # Check if any admin user exists
        admin_exists = db.users.find_one({'is_admin': True})
        
        if not admin_exists:
            print("Creating admin user...")
            admin_data = {
                'sponsor_id': 'AL0000001',
                'user_name': 'Admin',
                'email': 'admin@awardloop.com',
                'wallet_address': '0x0000000000000000000000000000000000000000',
                'security_pin': generate_password_hash('admin123', method='pbkdf2:sha256'),
                'balance': 0.00,
                'is_admin': True,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            db.users.insert_one(admin_data)
            print("Admin user created.")
        else:
            print("Admin user already exists.")
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to create admin user: {str(e)}")
        return False

# Run this if the file is executed directly
if __name__ == "__main__":
    init_mongodb()
    create_admin_user_if_not_exists()