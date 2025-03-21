# app/tasks/event_handlers.py
"""
Real-time event handlers for immediate process execution

This module provides event-driven automation for the AwardLoop platform,
triggering immediate actions when certain conditions are met without
waiting for scheduled tasks.
"""

import logging
from datetime import datetime
from app import create_app
from app.tasks.automated_distributions import (
    distribute_roi,
    distribute_referral_income,
    collect_admin_fees,
    manage_investment_cycles
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("event_handlers.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def handle_bid_cycle_filled(cycle_id):
    """
    Handle immediate processing when a bid cycle becomes filled
    
    Args:
        cycle_id: ID of the filled bid cycle
    """
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        
        try:
            logger.info(f"Processing filled bid cycle #{cycle_id} immediately")
            
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Convert string ID to ObjectId if needed
            if isinstance(cycle_id, str):
                try:
                    cycle_id_obj = ObjectId(cycle_id)
                except:
                    cycle_id_obj = cycle_id
            else:
                cycle_id_obj = cycle_id
            
            # Get the bid cycle using MongoDB
            cycle = db.bid_cycles.find_one({"_id": cycle_id_obj})
            
            if not cycle:
                logger.error(f"Bid cycle #{cycle_id} not found")
                return False
            
            # Check if cycle is actually full
            if cycle.get('bids_filled', 0) >= cycle.get('total_bids_allowed', 0):
                # Mark as closed using MongoDB update
                db.bid_cycles.update_one(
                    {"_id": cycle_id_obj},
                    {"$set": {
                        "cycle_status": "closed",
                        "close_time": datetime.utcnow()
                    }}
                )
                
                # Update system setting using MongoDB
                db.system_settings.update_one(
                    {"setting_key": "bid_cycle_status"},
                    {"$set": {"setting_value": "closed"}}
                )
                
                # Log the activity using MongoDB insert
                db.system_log.insert_one({
                    "log_type": "bid_cycle_filled_closed",
                    "log_message": f"Bid cycle #{cycle_id} automatically closed after reaching capacity: {cycle.get('bids_filled')}/{cycle.get('total_bids_allowed')} units",
                    "created_at": datetime.utcnow()
                })
                
                logger.info(f"Bid cycle #{cycle_id} marked as closed")
                
                # Immediately trigger the next cycle to open
                open_next_bid_cycle()
                
                return True
            else:
                logger.info(f"Bid cycle #{cycle_id} is not actually full: {cycle.get('bids_filled')}/{cycle.get('total_bids_allowed')}")
                return False
                
        except Exception as e:
            logger.exception(f"Error handling filled bid cycle: {str(e)}")
            return False

def open_next_bid_cycle():
    """
    Immediately open the next bid cycle after one fills up
    """
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        
        try:
            logger.info("Opening next bid cycle immediately")
            
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Get the current datetime with proper timezone
            from datetime import datetime
            import pytz
            from app.models.system_settings import SystemSettings
            
            # Get timezone from settings for consistent time handling
            timezone_str = SystemSettings.get_value('bid_timezone', 'Asia/Kolkata')
            timezone = pytz.timezone(timezone_str)
            
            # Create timezone-aware UTC now time
            now_naive = datetime.utcnow()
            now_aware = pytz.utc.localize(now_naive)
            now_local = now_aware.astimezone(timezone)
            
            # Check if there's already an open cycle using MongoDB
            current_cycle = db.bid_cycles.find_one({"cycle_status": "open"})
            
            if current_cycle:
                logger.info(f"Bid cycle #{current_cycle.get('_id')} is already open")
                return False
            
            # Get the last cycle to determine the new unit count using MongoDB
            last_cycle = db.bid_cycles.find_one(
                {}, 
                sort=[("_id", -1)]  # Sort by _id descending to get the most recent
            )
            
            cycle_number = 0
            if last_cycle:
                # Calculate days since first cycle
                first_cycle = db.bid_cycles.find_one(
                    {}, 
                    sort=[("_id", 1)]  # Sort by _id ascending to get the first one
                )
                
                # Calculate days elapsed if first_cycle exists and has cycle_date
                if first_cycle and 'cycle_date' in first_cycle:
                    first_cycle_date = first_cycle.get('cycle_date')
                    # Handle both date and datetime objects for compatibility
                    if isinstance(first_cycle_date, datetime):
                        first_date = first_cycle_date.date()
                    else:
                        first_date = first_cycle_date
                    
                    days_elapsed = (now_local.date() - first_date).days
                    cycle_number = days_elapsed // 5  # 5 days per cycle
            
            # Get bid limit from unit progression table using MongoDB
            progression = db.unit_progression.find_one({"cycle_number": cycle_number})
            
            if not progression:
                # Default to 5 if not found
                total_bids = 5
            else:
                total_bids = progression.get('units_allowed', 5)
            
            # Get or create cycle configuration from system settings
            # Get next cycle trigger configuration
            try:
                next_cycle_trigger_config = {
                    "only_open_when_filled": SystemSettings.get_value("only_open_when_filled", "true").lower() == "true",
                    "open_time": SystemSettings.get_value("bid_open_time", "00:10:00"),
                    "timezone": SystemSettings.get_value("bid_timezone", "Asia/Kolkata")
                }
            except Exception as e:
                logger.warning(f"Error getting next_cycle_trigger settings: {str(e)}. Using defaults.")
                next_cycle_trigger_config = {
                    "only_open_when_filled": True,
                    "open_time": "00:10:00",
                    "timezone": "Asia/Kolkata"
                }
                
            # Get cycle conditions configuration
            try:
                cycle_conditions_config = {
                    "auto_close_when_filled": SystemSettings.get_value("auto_close_when_filled", "true").lower() == "true",
                    "profit_distribution_day": float(SystemSettings.get_value("profit_distribution_day", "0.006"))
                }
            except Exception as e:
                logger.warning(f"Error getting cycle_conditions settings: {str(e)}. Using defaults.")
                cycle_conditions_config = {
                    "auto_close_when_filled": True,
                    "profit_distribution_day": 0.006
                }
            
            # Create a new cycle using MongoDB insert with proper datetime handling
            # Convert date to datetime for MongoDB compatibility
            cycle_date_datetime = datetime.combine(now_local.date(), datetime.min.time())
            
            # Create a timezone-aware open_time (now in the local timezone)
            open_time = timezone.localize(cycle_date_datetime.replace(
                hour=now_local.hour,
                minute=now_local.minute,
                second=now_local.second
            ))
            
            # Build the complete cycle document with all fields
            new_cycle_data = {
                "cycle_date": cycle_date_datetime,
                "total_bids_allowed": total_bids,
                "bids_filled": 0,
                "cycle_status": "open",
                "open_time": open_time,
                "close_time": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "next_cycle_trigger": next_cycle_trigger_config,
                "cycle_conditions": cycle_conditions_config
            }
            
            # Insert the new cycle document
            new_cycle_id = db.bid_cycles.insert_one(new_cycle_data).inserted_id
            
            # Update system setting using MongoDB
            db.system_settings.update_one(
                {"setting_key": "bid_cycle_status"},
                {"$set": {"setting_value": "open"}}
            )
                
            logger.info(f"New bid cycle opened immediately: #{new_cycle_id} with {total_bids} units available")
            
            # Log the activity using MongoDB insert
            db.system_log.insert_one({
                "log_type": "bid_cycle_opened_immediately",
                "log_message": f"New bid cycle #{new_cycle_id} opened immediately after previous cycle filled",
                "created_at": datetime.utcnow()
            })
            
            # Update cycle progression for the next cycle
            manage_investment_cycles()
            
            return True
                
        except Exception as e:
            logger.exception(f"Error opening next bid cycle: {str(e)}")
            return False

def process_filled_bid_cycle_distributions(cycle_id):
    """
    Process all financial distributions immediately when a cycle fills
    
    Args:
        cycle_id: ID of the filled bid cycle
    """
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        
        try:
            logger.info(f"Processing financial distributions for filled cycle #{cycle_id}")
            
            # Collect admin fees
            collect_admin_fees()
            
            # Distribute ROI for mature investments
            distribute_roi()
            
            # Distribute pending referral income
            distribute_referral_income()
            
            logger.info(f"Financial distributions for cycle #{cycle_id} completed")
            return True
                
        except Exception as e:
            logger.exception(f"Error processing distributions for filled cycle: {str(e)}")
            return False

def handle_bid_placed(bid_id, user_id, cycle_id):
    """
    Handle a new bid placement - check if cycle is now full
    
    Args:
        bid_id: ID of the new bid
        user_id: ID of the user who placed the bid
        cycle_id: ID of the bid cycle
    """
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        
        try:
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Convert string ID to ObjectId if needed
            if isinstance(cycle_id, str):
                try:
                    cycle_id_obj = ObjectId(cycle_id)
                except:
                    cycle_id_obj = cycle_id
            else:
                cycle_id_obj = cycle_id
                
            # Get the bid cycle using MongoDB
            cycle = db.bid_cycles.find_one({"_id": cycle_id_obj})
            
            if not cycle:
                logger.error(f"Bid cycle #{cycle_id} not found")
                return
            
            # Check if this bid filled the cycle
            if cycle.get('bids_filled', 0) >= cycle.get('total_bids_allowed', 0):
                logger.info(f"Bid #{bid_id} by user #{user_id} filled cycle #{cycle_id}")
                
                # Handle the filled cycle
                handle_bid_cycle_filled(cycle_id)
                
                # Process distributions
                process_filled_bid_cycle_distributions(cycle_id)
            else:
                remaining = cycle.get('total_bids_allowed', 0) - cycle.get('bids_filled', 0)
                logger.info(f"Bid #{bid_id} placed. Cycle #{cycle_id} has {remaining} units remaining")
                
        except Exception as e:
            logger.exception(f"Error handling bid placement: {str(e)}")