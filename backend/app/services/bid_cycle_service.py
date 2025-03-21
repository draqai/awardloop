# app/services/bid_cycle_service.py
from app import db
from app.models.bid_cycles import BidCycle
from app.models.system_settings import SystemSettings
from app.models.unit_progression import UnitProgression
from datetime import datetime, timedelta
import pytz
from bson import ObjectId

class BidCycleService:
    @staticmethod
    def get_current_cycle():
        """Get the current active bid cycle, or create one if none exists"""
        # Get timezone from settings
        timezone_str = SystemSettings.get_value('bid_timezone', 'Asia/Kolkata')
        timezone = pytz.timezone(timezone_str)
        
        # Check if there's an open cycle
        open_cycle = None
        open_cycles = BidCycle.find_by_status('open')
        if open_cycles and len(open_cycles) > 0:
            open_cycle = open_cycles[0]
            return open_cycle
        
        # Check if there's a pending cycle for today
        today_date = datetime.now(timezone).date()
        
        # Convert date to datetime for MongoDB compatibility
        # MongoDB cannot encode datetime.date objects directly
        today_start = datetime.combine(today_date, datetime.min.time())
        
        # Find pending cycles for today
        pending_cycles = db[BidCycle.COLLECTION].find({
            "cycle_date": today_start,  # Use datetime object instead of date
            "cycle_status": "pending"
        })
        
        pending_cycle_list = list(pending_cycles)
        if pending_cycle_list:
            # Convert to BidCycle object
            pending_cycle = BidCycle._from_dict(pending_cycle_list[0])
            return pending_cycle
        
        # No active cycle, create one for today
        # First, determine which cycle number we're on
        last_cycle_data = db[BidCycle.COLLECTION].find_one(
            sort=[("_id", -1)]  # Sort by _id descending to get the latest
        )
        
        cycle_number = 1  # Default to first cycle
        
        if last_cycle_data:
            last_cycle = BidCycle._from_dict(last_cycle_data)
            # If the last cycle was within the last 5 days and completed, 
            # we're still in the same cycle group
            five_days_ago_date = (datetime.now(timezone) - timedelta(days=5)).date()
            # Convert date to datetime for MongoDB compatibility
            five_days_ago = datetime.combine(five_days_ago_date, datetime.min.time())
            
            if last_cycle.cycle_date >= five_days_ago_date:
                # Same cycle group, count how many complete cycles
                complete_cycles_count = db[BidCycle.COLLECTION].count_documents({
                    "cycle_date": {"$gte": five_days_ago},  # Use datetime object instead of date
                    "cycle_status": "closed"
                })
                
                # If we completed all 5 days, move to next cycle group
                last_cycle_id = str(last_cycle.id).split('_')[-1] if isinstance(last_cycle.id, str) else last_cycle.id
                if complete_cycles_count >= 5:
                    cycle_number = (last_cycle_id // 5) + 1 if isinstance(last_cycle_id, int) else 1
                else:
                    cycle_number = last_cycle_id // 5 if isinstance(last_cycle_id, int) else 0
        
        # Get the allowed bids for this cycle
        unit_data = None
        unit_data_cursor = db.unit_progression.find({"cycle_number": cycle_number})
        unit_data_list = list(unit_data_cursor)
        if unit_data_list:
            unit_data = unit_data_list[0]
        
        if not unit_data:
            # Fallback to first cycle if not found
            unit_data_cursor = db.unit_progression.find({"cycle_number": 0})
            unit_data_list = list(unit_data_cursor)
            if unit_data_list:
                unit_data = unit_data_list[0]
        
        units_allowed = unit_data.get('units_allowed', 5) if unit_data else 5
        
        # Create bid open time based on the system settings (default 8:10 AM in the configured timezone)
        open_time_str = SystemSettings.get_value('bid_open_time', '08:10:00')
        open_time_parts = [int(x) for x in open_time_str.split(':')]
        today_open = timezone.localize(
            datetime.combine(today_date, datetime.min.time().replace(
                hour=open_time_parts[0], 
                minute=open_time_parts[1] if len(open_time_parts) > 1 else 0,
                second=open_time_parts[2] if len(open_time_parts) > 2 else 0
            ))
        )
        
        # Get cycle configuration from system settings
        # Get next cycle trigger configuration
        try:
            next_cycle_trigger_config = {
                "only_open_when_filled": SystemSettings.get_value("only_open_when_filled", "true").lower() == "true",
                "open_time": open_time_str,  # Use the same open_time value
                "timezone": timezone_str
            }
        except Exception as e:
            print(f"Error getting next_cycle_trigger settings: {str(e)}. Using defaults.")
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
            print(f"Error getting cycle_conditions settings: {str(e)}. Using defaults.")
            cycle_conditions_config = {
                "auto_close_when_filled": True,
                "profit_distribution_day": 0.006
            }
        
        # Create new bid cycle - use datetime object for cycle_date instead of date
        cycle_date_datetime = datetime.combine(today_date, datetime.min.time())
        new_cycle = BidCycle(
            cycle_date=cycle_date_datetime,  # Use datetime object instead of date
            total_bids_allowed=units_allowed,
            bids_filled=0,
            cycle_status='pending',
            open_time=today_open,
            next_cycle_trigger=next_cycle_trigger_config,
            cycle_conditions=cycle_conditions_config
        )
        
        # Save to MongoDB
        new_cycle.save()
        
        return new_cycle
    
    @staticmethod
    def open_cycle_if_time():
        """Check if it's time to open the bid cycle"""
        cycle = BidCycleService.get_current_cycle()
        
        # If it's already open, nothing to do
        if cycle.cycle_status == 'open':
            return cycle
        
        # Get timezone from settings for consistent time comparison
        timezone_str = SystemSettings.get_value('bid_timezone', 'Asia/Kolkata')
        timezone = pytz.timezone(timezone_str)
        
        # Create timezone-aware now time for accurate comparison
        now_naive = datetime.utcnow()
        now_aware = pytz.utc.localize(now_naive)
        
        # If current time is past the open time, open the cycle
        if cycle.open_time and now_aware >= cycle.open_time:
            cycle.cycle_status = 'open'
            # Update the system setting to reflect open status
            SystemSettings.set_value('bid_cycle_status', 'open')
            # Save changes to MongoDB
            cycle.save()
        
        return cycle
    
    @staticmethod
    def close_cycle_if_filled():
        """Close the cycle if all bids are filled"""
        cycle = BidCycleService.get_current_cycle()
        
        # If already closed, nothing to do
        if cycle.cycle_status == 'closed':
            return cycle
        
        # If all bids are filled, close the cycle
        if cycle.bids_filled >= cycle.total_bids_allowed:
            cycle.cycle_status = 'closed'
            cycle.close_time = datetime.utcnow()
            # Update the system setting to reflect closed status
            SystemSettings.set_value('bid_cycle_status', 'closed')
            # Save changes to MongoDB
            cycle.save()
            
            # Immediately process distributions and open next cycle without waiting for scheduler
            from app.tasks.event_handlers import process_filled_bid_cycle_distributions, open_next_bid_cycle
            
            # Process distributions immediately
            process_filled_bid_cycle_distributions(str(cycle.id))
            
            # Open the next cycle immediately
            open_next_bid_cycle()
            
            # Log immediate processing
            from app.models.system_log import SystemLog
            log_data = {
                "log_type": "immediate_cycle_processing",
                "log_message": f"Bid cycle #{cycle.id} immediately processed upon detection as filled",
                "created_at": datetime.utcnow()
            }
            db.system_logs.insert_one(log_data)
        
        return cycle