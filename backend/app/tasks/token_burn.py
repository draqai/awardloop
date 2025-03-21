# app/tasks/token_burn.py
from app.services.token_service import TokenService
from app import db
import schedule
import time
import threading

def burn_daily_tokens():
    """
    Daily task to burn 0.5% of admin fees
    This creates scarcity and adds value to the LOOP token
    """
    token_service = TokenService()
    
    # Get total admin fees collected for the day
    from app.models.transactions import Transaction
    from datetime import datetime, timedelta
    
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    admin_fees = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'fee',
        Transaction.created_at >= yesterday
    ).scalar() or 0
    
    # Calculate burn amount (0.5% of admin fees)
    burn_amount = float(admin_fees) * 0.005
    
    if burn_amount <= 0:
        print(f"No tokens to burn today. Admin fees: {admin_fees}")
        return
    
    # Burn tokens
    success, result = token_service.burn_tokens(burn_amount)
    
    if success:
        print(f"Successfully burned {burn_amount} LOOP tokens")
    else:
        print(f"Failed to burn tokens: {result}")

def start_scheduler():
    """Start the scheduler for token burning"""
    # Schedule token burn daily at midnight
    schedule.every().day.at("00:00").do(burn_daily_tokens)
    
    # Run continuously
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def init_scheduler():
    """Initialize token burn scheduler in a separate thread"""
    thread = threading.Thread(target=start_scheduler)
    thread.daemon = True
    thread.start()