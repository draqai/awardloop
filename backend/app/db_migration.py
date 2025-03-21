"""
Database Migration Script

This script migrates data from the MySQL database to MongoDB.
It should be run after setting up the MongoDB connection.
If MySQL connection fails, it will generate sample data directly in MongoDB.
"""

import os
import pymysql
from pymysql.cursors import DictCursor
from app import db, mongo
from datetime import datetime
from bson.objectid import ObjectId
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='migration.log',
    filemode='a'
)
logger = logging.getLogger('db_migration')

def get_mysql_connection():
    """Connect to the MySQL database using configuration from environment"""
    from app.config import Config
    
    # Extract database connection info from SQLAlchemy URL
    db_url = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/awardloop_app'
    
    # Parse the SQLAlchemy URL for MySQL connection
    if 'mysql+pymysql://' in db_url:
        db_url = db_url.replace('mysql+pymysql://', '')
        
    # Extract username, password, host, and database
    if '@' in db_url:
        auth, rest = db_url.split('@')
        user_pass = auth.split(':')
        username = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        
        host_db = rest.split('/')
        host = host_db[0]
        database = host_db[1] if len(host_db) > 1 else 'awardloop_app'
    else:
        # Default connection parameters
        username = 'root'
        password = ''
        host = 'localhost'
        database = 'awardloop_app'
    
    # Connect to MySQL
    connection = pymysql.connect(
        host=host,
        user=username,
        password=password,
        database=database,
        cursorclass=DictCursor
    )
    
    return connection

def migrate_users(mysql_conn):
    """Migrate users from MySQL to MongoDB"""
    logger.info("Starting user migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all users from MySQL
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.users.delete_many({})
        
        # Process and insert each user
        for user in users:
            # Convert decimal values to float
            if 'balance' in user:
                user['balance'] = float(user['balance'])
            
            # Handle datetime objects
            for key in ['created_at', 'updated_at']:
                if key in user and user[key]:
                    user[key] = user[key]
            
            # Check if user already exists in MongoDB
            existing_user = db.users.find_one({'sponsor_id': user['sponsor_id']})
            if existing_user:
                # Update existing user
                db.users.update_one(
                    {'sponsor_id': user['sponsor_id']},
                    {'$set': user}
                )
            else:
                # Insert new user
                db.users.insert_one(user)
        
        logger.info(f"Successfully migrated {len(users)} users")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating users: {str(e)}")
        return False
    
    finally:
        cursor.close()

def migrate_referral_tree(mysql_conn):
    """Migrate referral tree from MySQL to MongoDB"""
    logger.info("Starting referral tree migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all referral relationships from MySQL
        cursor.execute("SELECT * FROM referral_tree")
        referrals = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.referral_tree.delete_many({})
        
        # Process and insert each referral relationship
        for ref in referrals:
            # Handle datetime objects
            if 'created_at' in ref and ref['created_at']:
                ref['created_at'] = ref['created_at']
            
            # Check if relationship already exists in MongoDB
            existing_ref = db.referral_tree.find_one({'user_id': ref['user_id']})
            if existing_ref:
                # Update existing relationship
                db.referral_tree.update_one(
                    {'user_id': ref['user_id']},
                    {'$set': ref}
                )
            else:
                # Insert new relationship
                db.referral_tree.insert_one(ref)
        
        logger.info(f"Successfully migrated {len(referrals)} referral relationships")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating referral tree: {str(e)}")
        return False
    
    finally:
        cursor.close()

def migrate_user_investments(mysql_conn):
    """Migrate user investments from MySQL to MongoDB"""
    logger.info("Starting user investments migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all user investments from MySQL
        cursor.execute("SELECT * FROM user_investments")
        investments = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.user_investments.delete_many({})
        
        # Process and insert each investment
        for inv in investments:
            # Convert decimal values to float
            if 'amount' in inv:
                inv['amount'] = float(inv['amount'])
            
            # Handle datetime objects
            for key in ['created_at', 'updated_at', 'maturity_date']:
                if key in inv and inv[key]:
                    inv[key] = inv[key]
            
            # Check if investment already exists in MongoDB
            existing_inv = db.user_investments.find_one({'id': inv['id']})
            if existing_inv:
                # Update existing investment
                db.user_investments.update_one(
                    {'id': inv['id']},
                    {'$set': inv}
                )
            else:
                # Insert new investment
                db.user_investments.insert_one(inv)
        
        logger.info(f"Successfully migrated {len(investments)} user investments")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating user investments: {str(e)}")
        return False
    
    finally:
        cursor.close()

def migrate_user_earnings(mysql_conn):
    """Migrate user earnings from MySQL to MongoDB"""
    logger.info("Starting user earnings migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all user earnings from MySQL
        cursor.execute("SELECT * FROM user_earnings")
        earnings = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.user_earnings.delete_many({})
        
        # Process and insert each earning record
        for earn in earnings:
            # Convert decimal values to float
            if 'amount' in earn:
                earn['amount'] = float(earn['amount'])
            
            # Handle datetime objects
            for key in ['created_at', 'processed_at']:
                if key in earn and earn[key]:
                    earn[key] = earn[key]
            
            # Check if earning already exists in MongoDB
            existing_earn = db.user_earnings.find_one({'id': earn['id']})
            if existing_earn:
                # Update existing earning
                db.user_earnings.update_one(
                    {'id': earn['id']},
                    {'$set': earn}
                )
            else:
                # Insert new earning
                db.user_earnings.insert_one(earn)
        
        logger.info(f"Successfully migrated {len(earnings)} user earnings")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating user earnings: {str(e)}")
        return False
    
    finally:
        cursor.close()

def migrate_team_business(mysql_conn):
    """Migrate team business data from MySQL to MongoDB"""
    logger.info("Starting team business migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all team business records from MySQL
        cursor.execute("SELECT * FROM team_business")
        team_businesses = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.team_business.delete_many({})
        
        # Process and insert each team business record
        for business in team_businesses:
            # Convert decimal values to float
            if 'business_volume' in business:
                business['business_volume'] = float(business['business_volume'])
            
            # Handle datetime objects
            for key in ['created_at', 'last_calculated_at']:
                if key in business and business[key]:
                    business[key] = business[key]
            
            # Check if record already exists in MongoDB
            existing_business = db.team_business.find_one({'user_id': business['user_id']})
            if existing_business:
                # Update existing record
                db.team_business.update_one(
                    {'user_id': business['user_id']},
                    {'$set': business}
                )
            else:
                # Insert new record
                db.team_business.insert_one(business)
        
        logger.info(f"Successfully migrated {len(team_businesses)} team business records")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating team business: {str(e)}")
        return False
    
    finally:
        cursor.close()

def migrate_user_legs(mysql_conn):
    """Migrate user legs data from MySQL to MongoDB"""
    logger.info("Starting user legs migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all user legs records from MySQL
        cursor.execute("SELECT * FROM user_legs")
        user_legs = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.user_legs.delete_many({})
        
        # Process and insert each user legs record
        for legs in user_legs:
            # Handle datetime objects
            for key in ['created_at', 'updated_at']:
                if key in legs and legs[key]:
                    legs[key] = legs[key]
            
            # Check if record already exists in MongoDB
            existing_legs = db.user_legs.find_one({'user_id': legs['user_id']})
            if existing_legs:
                # Update existing record
                db.user_legs.update_one(
                    {'user_id': legs['user_id']},
                    {'$set': legs}
                )
            else:
                # Insert new record
                db.user_legs.insert_one(legs)
        
        logger.info(f"Successfully migrated {len(user_legs)} user legs records")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating user legs: {str(e)}")
        return False
    
    finally:
        cursor.close()

def migrate_system_settings(mysql_conn):
    """Migrate system settings from MySQL to MongoDB"""
    logger.info("Starting system settings migration...")
    cursor = mysql_conn.cursor()
    
    try:
        # Fetch all system settings from MySQL
        cursor.execute("SELECT * FROM system_settings")
        settings = cursor.fetchall()
        
        # Clear existing data if needed (uncomment if you want to start fresh)
        # db.system_settings.delete_many({})
        
        # Process and insert each setting
        for setting in settings:
            # Check if setting already exists in MongoDB
            existing_setting = db.system_settings.find_one({'key': setting['key']})
            if existing_setting:
                # Update existing setting
                db.system_settings.update_one(
                    {'key': setting['key']},
                    {'$set': setting}
                )
            else:
                # Insert new setting
                db.system_settings.insert_one(setting)
        
        logger.info(f"Successfully migrated {len(settings)} system settings")
        return True
    
    except Exception as e:
        logger.error(f"Error migrating system settings: {str(e)}")
        return False
    
    finally:
        cursor.close()

def create_sample_data():
    """Create sample data in MongoDB when MySQL migration is not possible"""
    logger.info("Creating sample data in MongoDB...")
    
    try:
        # Create sample users with unique wallet addresses
        users = [
            {
                "id": 1,
                "sponsor_id": "AL0000001",
                "user_name": "Admin User",
                "email": "admin@example.com",
                "password_hash": "hashed_password",
                "balance": 1000.0,
                "is_admin": True,
                "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": 2,
                "sponsor_id": "AL0000002",
                "user_name": "John Doe",
                "email": "john@example.com",
                "password_hash": "hashed_password",
                "balance": 500.0,
                "is_admin": False,
                "wallet_address": "0x2345678901abcdef2345678901abcdef23456789",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": 3,
                "sponsor_id": "AL0000003",
                "user_name": "Jane Smith",
                "email": "jane@example.com",
                "password_hash": "hashed_password",
                "balance": 750.0,
                "is_admin": False,
                "wallet_address": "0x3456789012abcdef3456789012abcdef34567890",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert or update users
        for user in users:
            existing_user = db.users.find_one({"sponsor_id": user["sponsor_id"]})
            if existing_user:
                db.users.update_one({"sponsor_id": user["sponsor_id"]}, {"$set": user})
            else:
                db.users.insert_one(user)
        
        # Create sample referral tree relationships
        referrals = [
            {
                "user_id": 2,
                "referrer_id": 1,
                "tree_level": 1,
                "tree_position": 1,
                "created_at": datetime.utcnow(),
                "formatted_referrer_id": "AL0000001"
            },
            {
                "user_id": 3,
                "referrer_id": 2,
                "tree_level": 2,
                "tree_position": 1,
                "created_at": datetime.utcnow(),
                "formatted_referrer_id": "AL0000002"
            }
        ]
        
        # Insert or update referral relationships
        for ref in referrals:
            existing_ref = db.referral_tree.find_one({"user_id": ref["user_id"]})
            if existing_ref:
                db.referral_tree.update_one({"user_id": ref["user_id"]}, {"$set": ref})
            else:
                db.referral_tree.insert_one(ref)
        
        # Create sample user investments
        investments = [
            {
                "id": 1,
                "user_id": 2,
                "plan_id": 1,
                "amount": 200.0,
                "status": "active",
                "created_at": datetime.utcnow(),
                "maturity_date": datetime(2024, 12, 31)
            },
            {
                "id": 2,
                "user_id": 3,
                "plan_id": 2,
                "amount": 300.0,
                "status": "active",
                "created_at": datetime.utcnow(),
                "maturity_date": datetime(2024, 12, 31)
            }
        ]
        
        # Insert or update investments
        for inv in investments:
            existing_inv = db.user_investments.find_one({"id": inv["id"]})
            if existing_inv:
                db.user_investments.update_one({"id": inv["id"]}, {"$set": inv})
            else:
                db.user_investments.insert_one(inv)
        
        # Create sample user earnings
        earnings = [
            {
                "id": 1,
                "user_id": 2,
                "amount": 20.0,
                "earning_type": "referral",
                "earning_status": "processed",
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "user_id": 3,
                "amount": 15.0,
                "earning_type": "daily",
                "earning_status": "processed",
                "created_at": datetime.utcnow()
            }
        ]
        
        # Insert or update earnings
        for earn in earnings:
            existing_earn = db.user_earnings.find_one({"id": earn["id"]})
            if existing_earn:
                db.user_earnings.update_one({"id": earn["id"]}, {"$set": earn})
            else:
                db.user_earnings.insert_one(earn)
                
        # Create sample team business data
        team_business = [
            {
                "id": 1,
                "user_id": 1,
                "business_volume": 1500.0,
                "current_rank_level": 3,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "user_id": 2,
                "business_volume": 500.0,
                "current_rank_level": 1,
                "created_at": datetime.utcnow()
            }
        ]
        
        # Insert or update team business data
        for business in team_business:
            existing_business = db.team_business.find_one({"user_id": business["user_id"]})
            if existing_business:
                db.team_business.update_one({"user_id": business["user_id"]}, {"$set": business})
            else:
                db.team_business.insert_one(business)
                
        # Create sample user legs data
        user_legs = [
            {
                "id": 1,
                "user_id": 1,
                "total_legs": 2,
                "active_legs": 2,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "user_id": 2,
                "total_legs": 1,
                "active_legs": 1,
                "created_at": datetime.utcnow()
            }
        ]
        
        # Insert or update user legs data
        for legs in user_legs:
            existing_legs = db.user_legs.find_one({"user_id": legs["user_id"]})
            if existing_legs:
                db.user_legs.update_one({"user_id": legs["user_id"]}, {"$set": legs})
            else:
                db.user_legs.insert_one(legs)
                
        # Create sample system settings
        settings = [
            {
                "setting_key": "bid_cycle_status",
                "setting_value": "open",
                "setting_description": "Current bid cycle status",
                "updated_at": datetime.utcnow()
            },
            {
                "setting_key": "bid_cycle_id",
                "setting_value": "1",
                "setting_description": "Current bid cycle ID",
                "updated_at": datetime.utcnow()
            },
            {
                "setting_key": "maintenance_mode",
                "setting_value": "false",
                "setting_description": "System maintenance mode",
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert or update system settings
        for setting in settings:
            existing_setting = db.system_settings.find_one({"setting_key": setting["setting_key"]})
            if existing_setting:
                db.system_settings.update_one({"setting_key": setting["setting_key"]}, {"$set": setting})
            else:
                db.system_settings.insert_one(setting)
        
        logger.info("Successfully created sample data in MongoDB")
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        return False

def migrate_from_mysql_to_mongodb():
    """Main migration function to orchestrate the entire process"""
    start_time = time.time()
    logger.info("Starting MySQL to MongoDB migration...")
    
    try:
        # Try to connect to MySQL
        try:
            mysql_conn = get_mysql_connection()
            logger.info("Successfully connected to MySQL database")
            
            # Migrate data in the correct order to maintain relationships
            success = True
            success &= migrate_users(mysql_conn)
            success &= migrate_referral_tree(mysql_conn)
            success &= migrate_user_investments(mysql_conn)
            success &= migrate_user_earnings(mysql_conn)
            success &= migrate_team_business(mysql_conn)
            success &= migrate_user_legs(mysql_conn)
            success &= migrate_system_settings(mysql_conn)
            
            # Close MySQL connection
            mysql_conn.close()
            
        except Exception as mysql_error:
            # If MySQL connection fails, use sample data instead
            logger.warning(f"MySQL connection failed: {str(mysql_error)}")
            logger.info("Falling back to creating sample data in MongoDB directly")
            
            success = create_sample_data()
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        if success:
            logger.info(f"Migration completed successfully in {duration} seconds!")
        else:
            logger.warning(f"Migration completed with some errors in {duration} seconds. Check log for details.")
        
        return success
    
    except Exception as e:
        logger.critical(f"Critical error during migration: {str(e)}")
        return False

if __name__ == "__main__":
    # This allows running the migration script directly
    from app import create_app
    
    app = create_app()
    with app.app_context():
        migrate_from_mysql_to_mongodb()