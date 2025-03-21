# app/tasks/automated_distributions.py
import os
import logging
import datetime
import random
from decimal import Decimal
from app import db, create_app
from app.services.transaction_service import TransactionService
from app.services.token_service import TokenService
from app.services.system_service import get_system_setting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automated_distributions.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create an application context
app = create_app()

def distribute_referral_income():
    """
    Distribute referral income across 12 levels for all users
    This runs daily to ensure all referrers receive their commissions
    """
    with app.app_context():
        logger.info("Starting automated referral income distribution...")
        
        try:
            # Get all users with pending referral earnings
            from app.models.user_earnings import UserEarnings
            pending_earnings = UserEarnings.query.filter_by(
                earning_type='referral',
                earning_status='pending'
            ).all()
            
            if not pending_earnings:
                logger.info("No pending referral earnings found")
                return {"success": True, "message": "No pending earnings found"}
            
            # Process each pending earning
            transaction_service = TransactionService()
            processed_count = 0
            failed_count = 0
            total_amount = 0
            
            for earning in pending_earnings:
                try:
                    # Check if referrer is eligible to receive commissions
                    if transaction_service._check_referrer_eligibility(earning.user_id):
                        # Add commission to referrer balance and record
                        result = transaction_service.process_referral_commission(
                            user_id=earning.user_id,
                            amount=earning.amount,
                            source_user_id=earning.source_id
                        )
                        
                        if result['success']:
                            # Mark as processed
                            earning.earning_status = 'processed'
                            earning.processed_at = datetime.datetime.utcnow()
                            processed_count += 1
                            total_amount += float(earning.amount)
                            logger.info(f"Processed {earning.amount} USDT referral commission for user {earning.user_id}")
                        else:
                            failed_count += 1
                            logger.error(f"Failed to process referral commission for user {earning.user_id}: {result.get('message')}")
                    
                except Exception as e:
                    logger.exception(f"Error processing referral commission for user {earning.user_id}: {str(e)}")
                    failed_count += 1
                    continue
            
            db.session.commit()
            
            logger.info(f"Referral income distribution completed. Processed: {processed_count}, Failed: {failed_count}, Total amount: {total_amount}")
            return {
                "success": True,
                "processed": processed_count,
                "failed": failed_count,
                "total_amount": total_amount
            }
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error in referral income distribution: {str(e)}")
            return {"success": False, "message": str(e)}

def collect_admin_fees():
    """
    Process admin fee collection from all recent deposits
    Sends fees to external admin wallet address and allocates 8% for reward distributions
    """
    with app.app_context():
        logger.info("Starting admin fee collection...")
        
        try:
            # Get all unprocessed deposits
            from app.models.transaction import TatumTransaction
            from datetime import datetime, timedelta
            import os
            
            # Look for transactions in the last day that haven't had fees processed
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            transactions = TatumTransaction.query.filter(
                TatumTransaction.transaction_type.in_(['deposit', 'investment']),
                TatumTransaction.created_at >= yesterday,
                TatumTransaction.fee_processed.is_(False)
            ).all()
            
            if not transactions:
                logger.info("No transactions found for fee processing")
                return {"success": True, "message": "No transactions found"}
            
            # Get wallet addresses from environment variables
            admin_fee_wallet = os.environ.get('ADMIN_FEE_WALLET_ADDRESS')
            rewards_wallet = os.environ.get('REWARDS_WALLET_ADDRESS')
            rewards_wallet_key = os.environ.get('REWARDS_WALLET_PRIVATE_KEY')
            
            if not admin_fee_wallet or not rewards_wallet:
                logger.warning("Fee wallet addresses not configured. Using default admin account.")
                admin_fee_wallet = None
                rewards_wallet = None
            
            # Process each transaction
            admin_id = int(get_system_setting('admin_user_id', 1))
            fee_percentage = float(get_system_setting('admin_fee_percentage', 2.0))
            rewards_percentage = 8.0  # Fixed 8% allocation for rewards
            
            total_fees = 0
            total_rewards = 0
            processed_count = 0
            
            for tx in transactions:
                try:
                    # Calculate fees
                    fee_amount = tx.amount * (fee_percentage / 100)
                    rewards_amount = tx.amount * (rewards_percentage / 100)
                    
                    # Record admin fee transaction
                    fee_tx = TatumTransaction(
                        transaction_id=f"FEE-{tx.transaction_id}",
                        user_id=admin_id,
                        transaction_type='fee',
                        amount=fee_amount,
                        status='pending' if admin_fee_wallet else 'completed',
                        reference_id=str(tx.id)
                    )
                    db.session.add(fee_tx)
                    
                    # Record rewards fee transaction
                    rewards_tx = TatumTransaction(
                        transaction_id=f"REWARDS-{tx.transaction_id}",
                        user_id=admin_id,
                        transaction_type='rewards_allocation',
                        amount=rewards_amount,
                        status='pending' if rewards_wallet else 'completed',
                        reference_id=str(tx.id)
                    )
                    db.session.add(rewards_tx)
                    
                    # Mark original transaction as fee processed
                    tx.fee_processed = True
                    
                    total_fees += fee_amount
                    total_rewards += rewards_amount
                    processed_count += 1
                    
                except Exception as e:
                    logger.exception(f"Error processing fee for transaction {tx.id}: {str(e)}")
                    continue
            
            db.session.commit()
            
            # If we collected fees and have wallet addresses configured, send to external wallets
            if total_fees > 0 and admin_fee_wallet:
                # Send admin fees to external wallet
                from app.services.transaction_service import TransactionService
                transaction_service = TransactionService()
                
                # Create a pending transaction to send fees to admin wallet
                from app.models.pending_transaction import PendingTransaction
                admin_pending_tx = PendingTransaction(
                    source_user_id=admin_id,
                    destination_address=admin_fee_wallet,
                    amount=total_fees,
                    transaction_type='admin_fee',
                    status='pending',
                    created_at=datetime.utcnow()
                )
                db.session.add(admin_pending_tx)
                logger.info(f"Scheduled transfer of {total_fees} USDT admin fees to external wallet {admin_fee_wallet}")
            
            # If we allocated rewards and have the rewards wallet configured, send rewards
            if total_rewards > 0 and rewards_wallet and rewards_wallet_key:
                # Send rewards to external wallet for distributions
                from app.services.transaction_service import TransactionService
                transaction_service = TransactionService()
                
                # Create a pending transaction to send rewards to distribution wallet
                from app.models.pending_transaction import PendingTransaction
                rewards_pending_tx = PendingTransaction(
                    source_user_id=admin_id,
                    destination_address=rewards_wallet,
                    amount=total_rewards,
                    transaction_type='rewards_allocation',
                    status='pending',
                    created_at=datetime.utcnow()
                )
                db.session.add(rewards_pending_tx)
                logger.info(f"Scheduled transfer of {total_rewards} USDT (8% allocation) to rewards wallet {rewards_wallet}")
                
                # Store the breakdown of reward allocations as percentages of total transaction amount
                # Total adds up to 8%: 5% + 2.5% + 0.25% + 0.25% = 8%
                tx_total_amount = total_fees + total_rewards  # Total amount of processed transactions
                rewards_breakdown = {
                    'total': total_rewards,  # 8% of transaction amount
                    'referral_levels': tx_total_amount * 0.05,  # 5% for referral levels
                    'team_rewards': tx_total_amount * 0.025,    # 2.5% for team rewards
                    'loop_tokens': tx_total_amount * 0.0025,    # 0.25% for loop tokens
                    'social_media': tx_total_amount * 0.0025    # 0.25% for social media
                }
                
                # Log the breakdown
                logger.info(f"Rewards breakdown: {rewards_breakdown}")
            
            db.session.commit()
            
            logger.info(f"Admin fee collection completed. Processed: {processed_count}, Total admin fees: {total_fees}, Total rewards allocation: {total_rewards}")
            return {
                "success": True,
                "processed": processed_count,
                "total_admin_fees": total_fees,
                "total_rewards_allocation": total_rewards
            }
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error in admin fee collection: {str(e)}")
            return {"success": False, "message": str(e)}

def distribute_roi():
    """
    Distribute Return on Investment (ROI) for all active investments
    Uses a decentralized peer-to-peer model where payments come directly from active users
    Handles the 115% return after 5-day cycle (or extended cycle)
    Adapts cycle length based on available funds
    """
    with app.app_context():
        logger.info("Starting decentralized P2P ROI distribution...")
        
        try:
            # Get the default investment days from settings
            default_cycle_days = int(get_system_setting('investment_days', 5))
            current_cycle_days = default_cycle_days
            
            # Get all investments due for maturity payout
            from app.models.user_investments import UserInvestment
            from datetime import datetime, timedelta
            
            # Find investments that have reached maturity
            mature_investments = []
            
            # Get all active investments
            active_investments = UserInvestment.query.filter_by(
                investment_status='active'
            ).all()
            
            # Check which investments have reached maturity
            for inv in active_investments:
                days_active = (datetime.utcnow() - inv.activation_date).days
                if days_active >= inv.cycle_days:
                    mature_investments.append(inv)
            
            # If there are no mature investments, we're done
            if not mature_investments:
                logger.info("No mature investments found for ROI distribution")
                return {
                    "success": True,
                    "processed": 0,
                    "message": "No mature investments found"
                }
            
            # Calculate total needed for payouts
            total_payout_needed = sum([inv.amount * 1.15 for inv in mature_investments])
            
            # Get available funds from active investments
            from app.models.user_wallet import UserWallet
            
            # Get all wallets with balance
            wallets_with_balance = UserWallet.query.filter(
                UserWallet.balance > 0,
                UserWallet.wallet_type == 'user'
            ).all()
            
            # Calculate total available funds (approximate)
            available_funds = sum([wallet.balance for wallet in wallets_with_balance])
            
            # Check if we need to extend the cycle due to insufficient funds
            cycle_extension_needed = total_payout_needed > available_funds
            
            if cycle_extension_needed:
                # Calculate new cycle days (25% longer)
                current_cycle_days = int(default_cycle_days * 1.25)
                logger.info(f"Extending investment cycle to {current_cycle_days} days due to insufficient funds")
                
                # Update cycle days setting
                from app.models.system_settings import SystemSettings
                cycle_setting = SystemSettings.query.filter_by(setting_key='investment_days').first()
                if cycle_setting:
                    cycle_setting.setting_value = str(current_cycle_days)
                    db.session.commit()
                    
                # Update each investment's cycle days
                for inv in active_investments:
                    inv.cycle_days = current_cycle_days
                
                # Filter mature investments based on new cycle length
                mature_investments = [inv for inv in mature_investments if 
                                     (datetime.utcnow() - inv.activation_date).days >= current_cycle_days]
                
                # If no investments are still mature after extension, we're done
                if not mature_investments:
                    logger.info("No mature investments after cycle extension")
                    db.session.commit()
                    return {
                        "success": True,
                        "processed": 0,
                        "message": "Cycle extended, no mature investments"
                    }
            elif available_funds >= total_payout_needed * 2:  # If we have twice what's needed, revert to default
                # If funds are plentiful, revert to default cycle
                if current_cycle_days != 5:
                    logger.info(f"Reverting investment cycle to 5 days due to sufficient funds")
                    from app.models.system_settings import SystemSettings
                    cycle_setting = SystemSettings.query.filter_by(setting_key='investment_days').first()
                    if cycle_setting:
                        cycle_setting.setting_value = "5"
                        db.session.commit()
            
            # Process mature investments using peer-to-peer payments
            processed_count = 0
            failed_count = 0
            total_roi_paid = 0
            
            # Initialize the Tatum service for direct wallet transfers
            transaction_service = TransactionService()
            
            # Sort wallets by balance (highest first) to optimize distribution
            wallets_with_balance.sort(key=lambda w: w.balance, reverse=True)
            
            # Process each mature investment
            for investment in mature_investments:
                try:
                    # Calculate maturity amount (115% of investment)
                    maturity_amount = investment.amount * 1.15
                    roi_amount = maturity_amount - investment.amount  # 15% profit
                    
                    # Get user and their external wallet
                    from app.models.user import User
                    user = User.query.get(investment.user_id)
                    
                    if not user:
                        logger.error(f"User not found for investment {investment.id}")
                        failed_count += 1
                        continue
                    
                    # Get user's external wallet address
                    user_wallet = UserWallet.query.filter_by(
                        user_id=user.id,
                        wallet_type='external',
                        is_primary=True
                    ).first()
                    
                    if not user_wallet or not user_wallet.wallet_address:
                        logger.error(f"No external wallet found for user {user.id}")
                        # Fall back to internal balance
                        user.balance += maturity_amount
                        logger.info(f"Added ROI to internal balance for user {user.id} due to missing external wallet")
                    else:
                        # Implement peer-to-peer payment distribution
                        # Split payment into 3-4 parts from different source wallets
                        remaining_amount = maturity_amount
                        payment_parts = []
                        
                        # Initial number of parts for distribution
                        num_parts = min(4, len(wallets_with_balance))
                        
                        if num_parts == 0:
                            logger.error("No source wallets with balance available for distribution")
                            failed_count += 1
                            continue
                        
                        # Calculate amounts for each part
                        base_amount = maturity_amount / num_parts
                        
                        # Process each part as a separate transaction
                        for i in range(num_parts):
                            # Get source wallet
                            source_wallet = wallets_with_balance[i % len(wallets_with_balance)]
                            
                            # Calculate this part's amount (last part gets any remainder)
                            if i == num_parts - 1:
                                part_amount = remaining_amount
                            else:
                                # Add some randomness to amounts for privacy
                                variation = base_amount * 0.1  # 10% variation
                                part_amount = round(base_amount + random.uniform(-variation, variation), 2)
                                part_amount = min(part_amount, remaining_amount)
                            
                            # Ensure we don't exceed the source wallet's balance
                            part_amount = min(part_amount, source_wallet.balance)
                            
                            if part_amount <= 0:
                                continue
                                
                            # Record this payment part
                            payment_parts.append({
                                'source_wallet_id': source_wallet.id,
                                'source_user_id': source_wallet.user_id,
                                'amount': part_amount
                            })
                            
                            # Update remaining amount
                            remaining_amount -= part_amount
                            
                            # Update source wallet balance (pending actual blockchain transfer)
                            source_wallet.balance -= part_amount
                        
                        # Execute the blockchain transfers for each part
                        for part in payment_parts:
                            try:
                                # Get the source wallet info
                                source_wallet = UserWallet.query.get(part['source_wallet_id'])
                                
                                # Create transaction record
                                from app.models.transaction import TatumTransaction
                                transaction = TatumTransaction(
                                    transaction_id=f"ROI-{investment.id}-PART-{len(payment_parts)}",
                                    user_id=user.id,
                                    source_user_id=part['source_user_id'],
                                    transaction_type='investment_return',
                                    amount=part['amount'],
                                    status='pending',
                                    reference_id=str(investment.id)
                                )
                                db.session.add(transaction)
                                
                                # Execute the blockchain transaction
                                # Note: In production, you'd use transaction_service.send_usdt here
                                # For this implementation, we're simulating the blockchain transaction
                                
                                # Record in the pending transactions table for blockchain execution
                                from app.models.pending_transaction import PendingTransaction
                                pending_tx = PendingTransaction(
                                    source_wallet_id=source_wallet.id,
                                    destination_address=user_wallet.wallet_address,
                                    amount=part['amount'],
                                    transaction_type='roi',
                                    reference_id=str(investment.id),
                                    status='pending',
                                    created_at=datetime.utcnow()
                                )
                                db.session.add(pending_tx)
                                
                                logger.info(f"Scheduled P2P payment part: {part['amount']} USDT from wallet {source_wallet.id} to user {user.id}")
                                
                            except Exception as e:
                                logger.exception(f"Error processing payment part: {str(e)}")
                                # If one part fails, continue with others
                        
                        # If there's any remaining amount that couldn't be distributed
                        if remaining_amount > 0:
                            logger.warning(f"Could only distribute {maturity_amount - remaining_amount} of {maturity_amount} for investment {investment.id}")
                            # Add remaining to internal balance
                            user.balance += remaining_amount
                    
                    # Record earnings
                    from app.models.user_earnings import UserEarnings
                    earnings = UserEarnings(
                        user_id=user.id,
                        source_id=investment.id,
                        amount=roi_amount,
                        earning_type='roi',
                        earning_status='processed'
                    )
                    db.session.add(earnings)
                    
                    # Mark investment as completed
                    investment.investment_status = 'completed'
                    investment.completion_date = datetime.utcnow()
                    
                    # Record activity
                    from app.models.user_activity import UserActivity
                    activity = UserActivity(
                        user_id=user.id,
                        activity_type='investment_return',
                        activity_description=f"Received {maturity_amount} USDT (115% of {investment.amount}) in P2P distribution after {(datetime.utcnow() - investment.activation_date).days} days"
                    )
                    db.session.add(activity)
                    
                    processed_count += 1
                    total_roi_paid += maturity_amount
                    
                except Exception as e:
                    logger.exception(f"Error processing ROI for investment {investment.id}: {str(e)}")
                    failed_count += 1
                    continue
            
            db.session.commit()
            
            logger.info(f"Decentralized P2P ROI distribution completed. Processed: {processed_count}, Failed: {failed_count}, Total scheduled: {total_roi_paid}")
            return {
                "success": True,
                "processed": processed_count,
                "failed": failed_count,
                "total_paid": total_roi_paid,
                "cycle_days": current_cycle_days
            }
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error in ROI distribution: {str(e)}")
            return {"success": False, "message": str(e)}

def distribute_loop_token_rewards():
    """
    Distribute LOOP token rewards for social media participation
    Airdrops tokens to users who have participated in social media contests
    """
    with app.app_context():
        logger.info("Starting LOOP token rewards distribution...")
        
        try:
            # Get all pending token airdrops
            from app.models.token_airdrops import TokenAirdrop
            pending_airdrops = TokenAirdrop.query.filter_by(
                status='pending'
            ).all()
            
            if not pending_airdrops:
                logger.info("No pending token airdrops found")
                return {"success": True, "message": "No pending airdrops found"}
            
            # Process each airdrop
            token_service = TokenService()
            processed_count = 0
            failed_count = 0
            total_tokens = 0
            
            for airdrop in pending_airdrops:
                try:
                    # Send airdrop
                    success, tx_id = token_service.airdrop_tokens(
                        to_address=airdrop.wallet_address,
                        amount=airdrop.amount
                    )
                    
                    if success:
                        # Update airdrop status
                        airdrop.status = 'completed'
                        airdrop.tx_hash = tx_id
                        airdrop.completed_at = datetime.datetime.utcnow()
                        
                        # Record activity
                        from app.models.user_activity import UserActivity
                        
                        if airdrop.user_id:
                            activity = UserActivity(
                                user_id=airdrop.user_id,
                                activity_type='token_airdrop',
                                activity_description=f"Received {airdrop.amount} LOOP tokens airdrop for {airdrop.airdrop_type}"
                            )
                            db.session.add(activity)
                        
                        processed_count += 1
                        total_tokens += float(airdrop.amount)
                        logger.info(f"Processed {airdrop.amount} LOOP token airdrop to {airdrop.wallet_address}")
                    else:
                        # Mark as failed
                        airdrop.status = 'failed'
                        airdrop.notes = tx_id  # Contains error message
                        failed_count += 1
                        logger.error(f"Failed to airdrop tokens to {airdrop.wallet_address}: {tx_id}")
                    
                except Exception as e:
                    logger.exception(f"Error processing token airdrop: {str(e)}")
                    airdrop.status = 'failed'
                    airdrop.notes = str(e)
                    failed_count += 1
                    continue
            
            db.session.commit()
            
            logger.info(f"LOOP token distribution completed. Processed: {processed_count}, Failed: {failed_count}, Total tokens: {total_tokens}")
            return {
                "success": True,
                "processed": processed_count,
                "failed": failed_count,
                "total_tokens": total_tokens
            }
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error in LOOP token distribution: {str(e)}")
            return {"success": False, "message": str(e)}

def manage_investment_cycles():
    """
    Manage investment cycles and unit progression
    Handles cycle growth by approximately 25% after each cycle
    """
    with app.app_context():
        logger.info("Starting investment cycle management...")
        
        try:
            # Get current active cycle
            from app.models.bid_cycles import BidCycle
            current_cycle = BidCycle.query.filter_by(cycle_status='open').first()
            
            if not current_cycle:
                logger.info("No active bid cycle found")
                return {"success": True, "message": "No active cycle found"}
            
            # Get the cycle number based on days since first cycle
            from app.models.bid_cycles import BidCycle
            first_cycle = BidCycle.query.order_by(BidCycle.id).first()
            
            if not first_cycle:
                logger.info("No cycle history found")
                return {"success": True, "message": "No cycle history found"}
            
            days_elapsed = (datetime.datetime.utcnow().date() - first_cycle.cycle_date).days
            cycle_number = days_elapsed // 5  # 5 days per cycle
            
            # Check if we need to update the unit progression for the next cycle
            from app.models.unit_progression import UnitProgression
            next_cycle = cycle_number + 1
            next_progression = UnitProgression.query.filter_by(cycle_number=next_cycle).first()
            
            if not next_progression:
                # Get current cycle units
                current_progression = UnitProgression.query.filter_by(cycle_number=cycle_number).first()
                current_units = 5  # Default to 5 for first cycle
                
                if current_progression:
                    current_units = current_progression.units_allowed
                
                # Calculate next cycle units (30% growth rate, rounded)
                next_units = int(current_units * 1.3)
                
                # Create next cycle progression
                next_progression = UnitProgression(
                    cycle_number=next_cycle,
                    units_allowed=next_units,
                    start_date=datetime.datetime.utcnow().date() + datetime.timedelta(days=(5 - days_elapsed % 5))
                )
                
                db.session.add(next_progression)
                db.session.commit()
                
                logger.info(f"Created new unit progression for cycle {next_cycle} with {next_units} units")
            
            return {
                "success": True,
                "current_cycle": cycle_number,
                "next_cycle": next_cycle,
                "next_units": next_progression.units_allowed if next_progression else None
            }
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error in investment cycle management: {str(e)}")
            return {"success": False, "message": str(e)}

def run_all_distributions():
    """Run all automated distribution tasks in sequence"""
    try:
        logger.info("Starting all automated distributions...")
        
        with app.app_context():
            # 1. Collect admin fees and burn tokens
            collect_admin_fees()
            
            # 2. Distribute referral income
            distribute_referral_income()
            
            # 3. Distribute ROI for mature investments
            distribute_roi()
            
            # 4. Distribute team rewards (weekly task)
            if datetime.datetime.now().weekday() == 6:  # Sunday
                from app.tasks.scheduled_tasks import calculate_team_rewards
                calculate_team_rewards()
            
            # 5. Distribute LOOP token rewards
            distribute_loop_token_rewards()
            
            # 6. Manage investment cycles
            manage_investment_cycles()
            
            logger.info("All automated distributions completed successfully")
            
    except Exception as e:
        logger.exception(f"Error running automated distributions: {str(e)}")

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    run_all_distributions()