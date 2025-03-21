# app/tasks/scheduler.py
"""
Scheduler module for AwardLoop platform
Handles scheduler initialization and separates it from tasks to avoid circular imports
"""
import logging
import schedule
import threading
import time
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("scheduler")

def start_scheduler():
    """Start the task scheduler with appropriate timing"""
    # Import tasks here to avoid circular imports
    from app.tasks.scheduled_tasks import (
        open_daily_bid_cycle,
        close_bid_cycle,
        collect_admin_fees,
        distribute_daily_returns,
        distribute_roi,
        distribute_referral_income,
        distribute_loop_token_rewards,
        calculate_team_rewards,
        process_blockchain_transactions
    )
    from app.tasks.token_burn import burn_daily_tokens
    
    logger.info("Initializing task scheduler...")
    
    # 8 AM IST daily - Open bid cycle and distribute returns
    schedule.every().day.at("02:30").do(open_daily_bid_cycle)  # 8 AM IST = 2:30 UTC
    
    # Check closing every hour
    schedule.every().hour.do(close_bid_cycle)
    
    # Collect admin fees and burn tokens at midnight
    schedule.every().day.at("00:00").do(collect_admin_fees)
    schedule.every().day.at("00:15").do(burn_daily_tokens)
    
    # Distribute returns and ROI at different times to manage system load
    schedule.every().day.at("03:00").do(distribute_daily_returns)
    schedule.every().day.at("04:00").do(distribute_roi)
    
    # Distribute referral income at a less busy time
    schedule.every().day.at("06:00").do(distribute_referral_income)
    
    # Token rewards distribution at night
    schedule.every().day.at("20:00").do(distribute_loop_token_rewards)
    
    # Team rewards weekly on Sunday
    schedule.every().sunday.at("12:00").do(calculate_team_rewards)
    
    # Process blockchain transactions every 15 minutes
    schedule.every(15).minutes.do(process_blockchain_transactions)
    
    logger.info("Scheduler initialized with all tasks")
    
    # Run continuously
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def init_scheduler():
    """Initialize the task scheduler in a separate thread"""
    try:
        # Only initialize in production, not during testing
        import os
        if os.environ.get('TESTING') == 'True':
            logger.info("Skipping scheduler initialization in testing mode")
            return
        
        thread = threading.Thread(target=start_scheduler)
        thread.daemon = True
        thread.start()
        logger.info("Automated task scheduler initialized and running")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")

def run_all_tasks():
    """Run all scheduled tasks in sequence for manual execution"""
    # Import scheduled tasks here to avoid circular imports
    from app.tasks.scheduled_tasks import run_scheduled_tasks
    
    app = create_app()
    with app.app_context():
        run_scheduled_tasks()