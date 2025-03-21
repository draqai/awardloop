# app/tasks/scheduled_tasks.py
import os
import requests
import logging
import datetime
import time
import schedule
import threading
from app import create_app
from app.services.transaction_service import TransactionService
from app.services.token_service import TokenService
from app.services.system_service import get_system_setting
from app.tasks.automated_distributions import (
    distribute_referral_income,
    collect_admin_fees,
    distribute_roi,
    distribute_loop_token_rewards,
    manage_investment_cycles
)
from app.tasks.token_burn import burn_daily_tokens
from app.tasks.transaction_processor import process_pending_transactions, cleanup_old_transactions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduled_tasks.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Don't create a global app context - create fresh ones in each function
# This prevents socket issues in background threads

def distribute_daily_returns():
    """Distribute daily returns to all active investments"""
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Starting daily returns distribution...")
        
        try:
            transaction_service = TransactionService()
            result = transaction_service.distribute_daily_returns()
            
            if result['success']:
                logger.info(f"Daily returns distribution completed. Processed: {result.get('processed', 0)}, Completed: {result.get('completed', 0)}, Failed: {result.get('failed', 0)}")
            else:
                logger.error(f"Daily returns distribution failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logger.exception(f"Error in daily returns distribution: {str(e)}")
            
        logger.info("Daily returns distribution task finished")

def calculate_team_rewards():
    """Calculate and distribute team rewards"""
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Starting team rewards calculation...")
        
        try:
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Get all users with sufficient active legs using MongoDB queries
            min_legs = int(get_system_setting('min_legs_for_reward', 5))
            eligible_legs = list(db.user_legs.find({"active_legs": {"$gte": min_legs}}))
            
            if not eligible_legs:
                logger.info("No users with sufficient active legs found")
                return
            
            # Get team reward percentage (2.5%)
            team_reward_percentage = float(get_system_setting('team_reward_percentage', 2.5))
            logger.info(f"Using team reward percentage: {team_reward_percentage}%")
            
            # Get team reward levels - fallback for legacy compatibility
            reward_levels = list(db.team_rewards.find({"is_active": 1}))
            
            if not reward_levels:
                logger.warning("No active reward levels defined, will use fixed 2.5% calculation")
            
            # Process each eligible user
            transaction_service = TransactionService()
            processed_count = 0
            failed_count = 0
            total_amount = 0
            
            for legs in eligible_legs:
                try:
                    user_id = legs.get('user_id')
                    if isinstance(user_id, str):
                        try:
                            user_id = ObjectId(user_id)
                        except:
                            pass
                    
                    # Get user's business volume
                    business = db.team_business.find_one({"user_id": user_id})
                    
                    if not business:
                        continue
                    
                    # Verify equal business across all legs
                    leg_details = list(db.user_leg_details.find({"user_id": user_id}))
                    
                    # Check if we have enough details to verify
                    if not leg_details or len(leg_details) < 5:
                        logger.info(f"User {user_id} doesn't have enough leg details to verify equal business")
                        continue
                    
                    # Get business volumes for each leg
                    leg_volumes = [leg.get('business_volume', 0) for leg in leg_details if leg.get('is_active', False)]
                    
                    # Check if we have at least 5 active legs with business
                    if len(leg_volumes) < 5:
                        logger.info(f"User {user_id} doesn't have 5+ active legs with business")
                        continue
                    
                    # Check for equal business distribution
                    # We'll allow a 10% variance to account for minor differences
                    avg_volume = sum(leg_volumes) / len(leg_volumes)
                    equal_business = all(abs(volume - avg_volume) <= (avg_volume * 0.1) for volume in leg_volumes)
                    
                    if not equal_business:
                        logger.info(f"User {user_id} doesn't have equal business across legs")
                        continue
                        
                    logger.info(f"User {user_id} has 5+ active legs with equal business distribution")
                    
                    # Calculate reward based on 2.5% of total business volume
                    business_volume = business.get('business_volume', 0)
                    reward_amount = business_volume * (team_reward_percentage / 100)
                    rank_level = 1 # Default rank
                    
                    # For backward compatibility, still check reward levels if available
                    if reward_levels:
                        # Find matching reward level
                        reward_level = None
                        for level in sorted(reward_levels, key=lambda x: x.get('business_volume', 0), reverse=True):
                            if business_volume >= level.get('business_volume', 0):
                                reward_level = level
                                break
                        
                        if reward_level:
                            # Use the higher reward amount between calculation and table
                            rank_level = reward_level.get('rank_level', 1)
                            if float(reward_level.get('reward_amount', 0)) > reward_amount:
                                reward_amount = float(reward_level.get('reward_amount', 0))
                    
                    # Check if we should distribute reward
                    if reward_amount > 0:
                        # User has enough business volume for reward
                        result = transaction_service.process_team_reward(
                            user_id=user_id,
                            amount=float(reward_amount),
                            team_level=rank_level
                        )
                        
                        if result['success']:
                            # Update rank level if using reward levels
                            if reward_levels:
                                db.team_business.update_one(
                                    {"user_id": user_id},
                                    {"$set": {"current_rank_level": rank_level}}
                                )
                            processed_count += 1
                            total_amount += float(reward_amount)
                            logger.info(f"Team reward processed for user {user_id}: rank {rank_level}, amount {reward_amount} (2.5% of {business_volume})")
                        else:
                            failed_count += 1
                            logger.error(f"Failed to process team reward for user {user_id}: {result.get('message')}")
                    
                    # Update last calculated timestamp
                    db.team_business.update_one(
                        {"user_id": user_id},
                        {"$set": {"last_calculated_at": datetime.datetime.utcnow()}}
                    )
                    
                except Exception as e:
                    logger.exception(f"Error processing team reward for user {legs.get('user_id')}: {str(e)}")
                    failed_count += 1
                    continue
            
            logger.info(f"Team rewards calculation completed. Processed: {processed_count}, Failed: {failed_count}, Total amount: {total_amount}")
            
        except Exception as e:
            logger.exception(f"Error in team rewards calculation: {str(e)}")
            
        logger.info("Team rewards calculation task finished")


def process_blockchain_transactions():
    """Process pending blockchain transactions for P2P payments"""
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Starting blockchain transaction processing...")
        
        try:
            # Process a batch of pending transactions
            result = process_pending_transactions(batch_size=20)
            
            # Log the results
            if result.get('success'):
                processed = result.get('processed', 0)
                failed = result.get('failed', 0)
                total = result.get('total_amount', 0)
                logger.info(f"Processed {processed} blockchain transactions, failed: {failed}, total amount: {total}")
            else:
                logger.warning(f"Transaction processing failed: {result.get('message')}")
                
            # Clean up old transactions periodically (every 4 hours)
            current_hour = datetime.datetime.utcnow().hour
            if current_hour % 4 == 0:  # Run at hours 0, 4, 8, 12, 16, 20
                cleanup_result = cleanup_old_transactions()
                if cleanup_result.get('success'):
                    logger.info(f"Cleaned up {cleanup_result.get('cleaned', 0)} old transactions")
                    
        except Exception as e:
            logger.exception(f"Error processing blockchain transactions: {str(e)}")
            
        logger.info("Blockchain transaction processing task finished")

def open_daily_bid_cycle():
    """Open a new bid cycle for the day"""
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Checking if a new bid cycle needs to be opened...")
        
        try:
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # REQUIREMENT: A new cycle will ONLY open when the last cycle's units are bought completely
            # If not all units are bought, the cycle extends days (remains open indefinitely)
            
            # Check if there's already an open cycle - only one cycle can be open at a time
            open_cycle = db.bid_cycles.find_one({"cycle_status": "open"})
            
            if open_cycle:
                logger.info(f"Cycle #{open_cycle.get('_id')} is still open with {open_cycle.get('total_bids_allowed', 0) - open_cycle.get('bids_filled', 0)} units remaining")
                return
            
            # If no open cycle exists and there's a closed cycle, we need to check if it was filled
            last_cycle = db.bid_cycles.find_one(
                {"cycle_status": "closed"},
                sort=[("_id", -1)]  # Sort by _id descending to get the most recent
            )
            
            if last_cycle and last_cycle.get('bids_filled', 0) < last_cycle.get('total_bids_allowed', 0):
                logger.info(f"Last cycle #{last_cycle.get('_id')} was closed but not filled completely. Waiting for manual intervention.")
                return
                
            # Get the bid open time settings - will be used to set open_time for the new cycle
            from datetime import datetime, time as dt_time
            bid_open_time_str = get_system_setting('bid_open_time', '08:00:00')
            bid_timezone = get_system_setting('bid_timezone', 'Asia/Kolkata')
            
            # Get current time in the configured timezone
            from pytz import timezone
            tz = timezone(bid_timezone)
            now = datetime.now(tz)
            
            # Parse the open time
            open_time_parts = bid_open_time_str.split(':')
            target_time = dt_time(
                hour=int(open_time_parts[0]), 
                minute=int(open_time_parts[1] if len(open_time_parts) > 1 else 0),
                second=int(open_time_parts[2] if len(open_time_parts) > 2 else 0)
            )
            
            # Create a datetime for today with the target time
            target_datetime = datetime.combine(now.date(), target_time)
            target_datetime = tz.localize(target_datetime)
            
            # If current time is past the target time, we should open a new cycle
            if now.time() >= target_time:
                # Get the last cycle to determine the day's unit count
                last_cycle = db.bid_cycles.find_one(
                    {}, 
                    sort=[("_id", -1)]  # Sort by _id descending to get the most recent
                )
                
                cycle_number = 0
                if last_cycle:
                    # Calculate days since first cycle
                    cycle_date = last_cycle.get('cycle_date')
                    days_elapsed = (now.date() - cycle_date).days if cycle_date else 0
                    cycle_number = days_elapsed // 5  # 5 days per cycle
                
                # Get bid limit from unit progression table
                progression = db.unit_progression.find_one({"cycle_number": cycle_number})
                
                if not progression:
                    # Default to 5 if not found
                    total_bids = 5
                else:
                    total_bids = progression.get('units_allowed', 5)
                
                # Create a new cycle using MongoDB document
                new_cycle_id = db.bid_cycles.insert_one({
                    "cycle_date": now.date(),
                    "total_bids_allowed": total_bids,
                    "bids_filled": 0,
                    "cycle_status": "open",
                    "open_time": now
                }).inserted_id
                
                # Update system setting
                status_setting = db.system_settings.find_one({"setting_key": "bid_cycle_status"})
                if status_setting:
                    db.system_settings.update_one(
                        {"setting_key": "bid_cycle_status"},
                        {"$set": {"setting_value": "open"}}
                    )
                    
                logger.info(f"New bid cycle opened: #{new_cycle_id} with {total_bids} units available")
                
                # Log the activity
                db.system_log.insert_one({
                    "log_type": "bid_cycle_opened",
                    "log_message": f"New bid cycle #{new_cycle_id} opened with {total_bids} units",
                    "created_at": datetime.utcnow()
                })
                
                # Update cycle progression for the next cycle
                manage_investment_cycles()
            else:
                logger.info(f"It's not yet time to open today's bid cycle. Current: {now.time()}, Target: {target_time}")
                
        except Exception as e:
            logger.exception(f"Error opening bid cycle: {str(e)}")
            
        logger.info("Bid cycle check task finished")

def close_bid_cycle():
    """Close the current bid cycle if it's time"""
    # Create a fresh app context for this task
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Checking if the current bid cycle needs to be closed...")
        
        try:
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Check if there's an open cycle using MongoDB
            current_cycle = db.bid_cycles.find_one({"cycle_status": "open"})
            
            if not current_cycle:
                logger.info("No open bid cycle found")
                return
            
            # Get the current time
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            
            # Check if all available units are filled - ONLY condition for closing a cycle
            if current_cycle.get('bids_filled', 0) >= current_cycle.get('total_bids_allowed', 0):
                # Close the cycle using MongoDB update_one
                db.bid_cycles.update_one(
                    {"_id": current_cycle.get('_id')},
                    {"$set": {
                        "cycle_status": "closed",
                        "close_time": now
                    }}
                )
                
                # Update system setting using MongoDB
                db.system_settings.update_one(
                    {"setting_key": "bid_cycle_status"},
                    {"$set": {"setting_value": "closed"}}
                )
                
                # Log the activity using MongoDB insert_one
                db.system_log.insert_one({
                    "log_type": "bid_cycle_closed",
                    "log_message": f"Bid cycle #{current_cycle.get('_id')} closed after all {current_cycle.get('total_bids_allowed')} units were sold",
                    "created_at": datetime.utcnow()
                })
                
                logger.info(f"Bid cycle #{current_cycle.get('_id')} closed. All {current_cycle.get('total_bids_allowed')} units sold.")
                
                # Immediately open the next cycle after filling
                from app.tasks.event_handlers import open_next_bid_cycle
                open_next_bid_cycle()
                logger.info("Opening next bid cycle immediately after current cycle filled")
            else:
                # Cycle has units remaining - do not close regardless of time elapsed
                remaining = current_cycle.get('total_bids_allowed', 0) - current_cycle.get('bids_filled', 0)
                logger.info(f"Bid cycle #{current_cycle.get('_id')} remains open with {remaining} units remaining")
                
        except Exception as e:
            logger.exception(f"Error closing bid cycle: {str(e)}")
            
        logger.info("Bid cycle closing check finished")

def run_scheduled_tasks():
    """Run all scheduled tasks in sequence"""
    # Create a fresh app context for this function
    app = create_app()
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Starting scheduled tasks...")
        
        try:
            # Open daily bid cycle at 8 AM IST
            open_daily_bid_cycle()
            
            # Close bid cycle if needed
            close_bid_cycle()
            
            # Collect admin fees
            collect_admin_fees()
            
            # Distribute daily returns
            distribute_daily_returns()
            
            # Distribute ROI for mature investments
            distribute_roi()
            
            # Distribute pending referral income
            distribute_referral_income()
            
            # Distribute LOOP token rewards
            distribute_loop_token_rewards()
            
            # Process blockchain transactions for outgoing payments
            process_blockchain_transactions()
            
            # Calculate team rewards (weekly task - check if it's Sunday)
            if datetime.datetime.now().weekday() == 6:  # 6 is Sunday
                calculate_team_rewards()
                
            # Burn tokens daily
            burn_daily_tokens()
            
            logger.info("All scheduled tasks completed")
            
        except Exception as e:
            logger.exception(f"Error running scheduled tasks: {str(e)}")

# NOTE: Scheduler initialization moved to scheduler.py to prevent circular imports
# See app/tasks/scheduler.py for the init_scheduler function

if __name__ == "__main__":
    # This allows the script to be run directly for testing or manual execution
    app = create_app()
    with app.app_context():
        run_scheduled_tasks()