# app/services/transaction_service.py
import os
import requests
import json
from app import db
from datetime import datetime
import uuid
import logging
from app.services.tatum_hybrid_service import TatumHybridService
from app.services.encryption_service import EncryptionService

# Configure logging
logger = logging.getLogger(__name__)

# Try to import Web3, but handle case when it's not installed
try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 library not installed. Will use Tatum API as fallback.")
class TransactionService:
    # BSC USDT Contract address
    USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
    
    # BSC node endpoints
    BSC_NODES = [
        'https://bsc-dataseed.binance.org/',
        'https://bsc-dataseed1.defibit.io/',
        'https://bsc-dataseed1.ninicoin.io/',
        'https://bsc-dataseed2.defibit.io/',
        'https://bsc-mainnet.gateway.tatum.io/'
    ]
    
    # Standard ERC-20 ABI for token transfers
    ERC20_ABI = json.dumps([
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ])
    
    def __init__(self):
        self.tatum_service = TatumHybridService()
        self.encryption_service = EncryptionService()
    
    def send_usdt_via_web3(self, private_key, to_address, amount, from_address=None):
        """
        Send USDT directly using Web3 without relying on Tatum API
        
        Args:
            private_key: Private key of the sender's wallet
            to_address: Destination address
            amount: Amount to send in USDT
            from_address: Optional sender address (derived from private key if not provided)
            
        Returns:
            Dictionary with transaction status and details or error
        """
        if not WEB3_AVAILABLE:
            return None, "Web3 library not available. Please install it with 'pip install web3'"
        
        try:
            # Try connecting to BSC nodes until one works
            web3 = None
            for node_url in self.BSC_NODES:
                try:
                    logger.info(f"Trying to connect to BSC node: {node_url}")
                    web3 = Web3(Web3.HTTPProvider(node_url))
                    if web3.is_connected():
                        logger.info(f"Successfully connected to BSC node: {node_url}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to connect to node {node_url}: {str(e)}")
            
            if not web3 or not web3.is_connected():
                return None, "Failed to connect to any BSC node"
            
            # Load the token contract
            token_contract = web3.eth.contract(
                address=Web3.to_checksum_address(self.USDT_CONTRACT),
                abi=json.loads(self.ERC20_ABI)
            )
            
            # Get token decimals
            decimals = token_contract.functions.decimals().call()
            logger.info(f"Token decimals: {decimals}")
            
            # Convert amount to wei
            amount_in_wei = int(float(amount) * (10 ** decimals))
            logger.info(f"Amount in wei: {amount_in_wei}")
            
            # Get the sender's address from private key if not provided
            if not from_address:
                account = web3.eth.account.from_key(private_key)
                from_address = account.address
            
            # Ensure addresses are checksum addresses
            from_address = Web3.to_checksum_address(from_address)
            to_address = Web3.to_checksum_address(to_address)
            
            # Get current balance for verification
            current_balance = token_contract.functions.balanceOf(from_address).call()
            current_balance_human = current_balance / (10 ** decimals)
            logger.info(f"Current balance: {current_balance_human} USDT")
            
            if current_balance < amount_in_wei:
                return None, f"Insufficient USDT balance. Available: {current_balance_human}, Required: {amount}"
            
            # Get the nonce
            nonce = web3.eth.get_transaction_count(from_address)
            logger.info(f"Nonce: {nonce}")
            
            # Build the transaction
            token_tx = token_contract.functions.transfer(
                to_address,
                amount_in_wei
            ).build_transaction({
                'chainId': 56,  # BSC mainnet
                'gas': 100000,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Estimate gas (optional but recommended)
            estimated_gas = web3.eth.estimate_gas(token_tx)
            logger.info(f"Gas estimate: {estimated_gas}")
            
            # Update with estimated gas
            token_tx.update({'gas': estimated_gas})
            
            # Sign the transaction
            signed_tx = web3.eth.account.sign_transaction(token_tx, private_key)
            logger.info("Transaction signed successfully")
            
            # Send the transaction
            # Find the raw transaction attribute (different versions of Web3 use different names)
            raw_tx_attr = None
            for attr in ['rawTransaction', 'raw_transaction', 'raw']:
                if hasattr(signed_tx, attr):
                    raw_tx_attr = attr
                    logger.info(f"Found raw transaction at attribute: {attr}")
                    break
            
            if not raw_tx_attr:
                logger.error("Could not find raw transaction attribute")
                logger.info(f"SignedTransaction object attributes: {dir(signed_tx)}")
                return None, "Could not find raw transaction data. Web3 version incompatibility."
            
            # Send the transaction using the detected attribute
            tx_hash = web3.eth.send_raw_transaction(getattr(signed_tx, raw_tx_attr))
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for the transaction receipt
            logger.info("Waiting for transaction receipt...")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Transaction receipt: {receipt}")
            
            # Check if transaction was successful
            if receipt.status == 1:
                logger.info("Transaction successful!")
                
                # Get updated balance for verification
                updated_balance = token_contract.functions.balanceOf(from_address).call()
                updated_balance_human = updated_balance / (10 ** decimals)
                
                return {
                    'txId': tx_hash.hex(),
                    'receipt': receipt
                }, None
            else:
                return None, f"Transaction failed with status: {receipt.status}"
            
        except Exception as e:
            logger.error(f"Error sending USDT via Web3: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None, str(e)
    def process_referral_commission(self, user_id, amount, source_user_id=None):
        """
        Process referral commission for a user
        
        Args:
            user_id: ID of user receiving commission
            amount: Commission amount in USDT
            source_user_id: ID of user who triggered the commission
            
        Returns:
            Dictionary with status and details
        """
        try:
            # Get the user
            from app.models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Add commission to user's balance
            user.balance += amount
            
            # Record the transaction
            from app.models.transaction import TatumTransaction
            
            transaction = TatumTransaction(
                transaction_id=f"REF-{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                transaction_type='commission',
                amount=amount,
                status='completed',
                reference_id=str(source_user_id) if source_user_id else None
            )
            
            # Record in user_earnings
            from app.models.user_earnings import UserEarnings
            
            earnings = UserEarnings(
                user_id=user_id,
                source_id=source_user_id if source_user_id else None,
                amount=amount,
                earning_type='referral',
                earning_status='processed'
            )
            
            # Log the activity
            from app.models.user_activity import UserActivity
            
            activity = UserActivity(
                user_id=user_id,
                activity_type='commission_received',
                activity_description=f"Received {amount} USDT referral commission"
            )
            
            db.session.add(transaction)
            db.session.add(earnings)
            db.session.add(activity)
            db.session.commit()
            
            # Save transaction to MongoDB as well
            transaction.save()
            
            # Update user balance in MongoDB
            now = datetime.utcnow()
            db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "balance": user.balance,
                    "updated_at": now
                }}
            )
            print(f"[DEBUG] Updated MongoDB user {user_id} balance to {user.balance} after referral commission")
            
            return {"success": True, "amount": amount, "user_id": user_id}
            
        except Exception as e:
            db.session.rollback()
            print(f"Error processing referral commission: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def process_team_reward(self, user_id, amount, team_level):
        """
        Process team reward for a user
        
        Args:
            user_id: ID of user receiving reward
            amount: Reward amount in USDT
            team_level: Team level that triggered the reward
            
        Returns:
            Dictionary with status and details
        """
        try:
            # Get the user
            from app.models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Check if the user has income on hold
            from app.models.income_hold_status import IncomeHoldStatus
            hold_status = IncomeHoldStatus.query.filter_by(user_id=user_id).first()
            
            # If income is on hold, record but don't distribute
            if hold_status and hold_status.team_rewards_on_hold:
                # Record as pending
                from app.models.user_earnings import UserEarnings
                
                earnings = UserEarnings(
                    user_id=user_id,
                    source_id=None,
                    amount=amount,
                    earning_type='team_reward',
                    earning_level=team_level,
                    earning_status='pending'
                )
                
                # Also record in team_business_earnings but mark as pending
                from app.models.team_business_earnings import TeamBusinessEarnings
                
                team_earnings = TeamBusinessEarnings(
                    user_id=user_id,
                    amount=amount,
                    rank_level=team_level,
                    status='pending',
                    distribution_date=datetime.utcnow(),
                    description=f"Team reward pending due to income hold"
                )
                
                db.session.add(earnings)
                db.session.add(team_earnings)
                db.session.commit()
                
                return {
                    "success": True, 
                    "status": "pending", 
                    "message": "Team reward on hold due to income hold status"
                }
            
            # Add reward to user's balance
            user.balance += amount
            
            # Record the transaction
            from app.models.transaction import TatumTransaction
            
            transaction = TatumTransaction(
                transaction_id=f"TEAM-{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                transaction_type='team_reward',
                amount=amount,
                status='completed',
                reference_id=f"Level-{team_level}"
            )
            
            # Record in user_earnings
            from app.models.user_earnings import UserEarnings
            
            earnings = UserEarnings(
                user_id=user_id,
                source_id=None,
                amount=amount,
                earning_type='team_reward',
                earning_level=team_level,
                earning_status='processed'
            )
            
            # Record in dedicated team_business_earnings table
            from app.models.team_business_earnings import TeamBusinessEarnings
            
            # Get team business data for additional context
            from app.models.team_business import TeamBusiness
            business = TeamBusiness.query.filter_by(user_id=user_id).first()
            
            business_volume = 0
            if business:
                business_volume = business.business_volume
            
            team_earnings = TeamBusinessEarnings(
                user_id=user_id,
                amount=amount,
                rank_level=team_level,
                status='processed',
                distribution_date=datetime.utcnow(),
                business_volume=business_volume,
                transaction_id=transaction.transaction_id,
                description=f"Team reward for rank level {team_level} (2.5% of {business_volume} business volume)"
            )
            
            # Log the activity
            from app.models.user_activity import UserActivity
            
            activity = UserActivity(
                user_id=user_id,
                activity_type='team_reward_received',
                activity_description=f"Received {amount} USDT team reward for level {team_level}"
            )
            
            db.session.add(transaction)
            db.session.add(earnings)
            db.session.add(team_earnings)
            db.session.add(activity)
            db.session.commit()
            
            # Save transaction to MongoDB as well
            transaction.save()
            
            # Update user balance in MongoDB
            now = datetime.utcnow()
            db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "balance": user.balance,
                    "updated_at": now
                }}
            )
            print(f"[DEBUG] Updated MongoDB user {user_id} balance to {user.balance} after team reward")
            
            return {"success": True, "amount": amount, "user_id": user_id, "level": team_level}
            
        except Exception as e:
            db.session.rollback()
            print(f"Error processing team reward: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _get_decrypted_private_key(self, wallet_id, admin_id, reason):
        """
        Securely retrieve and decrypt a private key
        
        Args:
            wallet_id: ID of the wallet
            admin_id: ID of admin requesting the key
            reason: Reason for key access
            
        Returns:
            Decrypted private key or None if error
        """
        try:
            # Get the wallet
            from app.models.user_wallet import UserWallet
            wallet = UserWallet.query.get(wallet_id)
            
            if not wallet or not wallet.encrypted_private_key:
                print(f"Wallet {wallet_id} not found or has no encrypted key")
                return None
            
            # Decrypt the private key
            decrypted_key = self.encryption_service.decrypt_private_key(
                wallet.encrypted_private_key,
                wallet.user_id,
                admin_id,
                reason
            )
            
            return decrypted_key
            
        except Exception as e:
            print(f"Error decrypting private key: {str(e)}")
            return None
    
    def _get_admin_wallet_key(self, admin_id, reason):
        """
        Securely retrieve the admin wallet private key
        
        Args:
            admin_id: ID of admin requesting the key
            reason: Reason for key access
            
        Returns:
            Admin private key or None if error
        """
        try:
            # First check if we have an encrypted admin wallet
            from app.models.user_wallet import UserWallet
            admin_wallet = UserWallet.query.filter_by(
                wallet_type='system',
                blockchain='BSC'
            ).first()
            
            if admin_wallet and admin_wallet.encrypted_private_key:
                # Use encrypted key from database
                return self._get_decrypted_private_key(
                    admin_wallet.id,
                    admin_id,
                    reason
                )
            
            # Fallback to environment variable (less secure)
            admin_key = os.environ.get('ADMIN_PRIVATE_KEY')
            if admin_key:
                # Log the access for audit purposes
                from app.models.system_log import SystemLog
                log = SystemLog(
                    log_type='admin_key_access',
                    log_message=f"Admin key accessed from environment by user {admin_id}: {reason}"
                )
                db.session.add(log)
                db.session.commit()
                
                return admin_key
                
            return None
            
        except Exception as e:
            print(f"Error retrieving admin key: {str(e)}")
            return None
    
    def send_usdt(self, from_user_id, to_address, amount, admin_id=None, wallet_id=None, admin_private_key=None):
        """
        Send USDT from a user's balance to an external address
        
        Args:
            from_user_id: User ID sending funds
            to_address: Destination wallet address
            amount: Amount to send in USDT
            admin_id: ID of admin initiating the transaction (if applicable)
            wallet_id: ID of the wallet to use (if applicable)
            admin_private_key: Legacy parameter - will be deprecated
            
        Returns:
            Dictionary with transaction status and details
        """
        try:
            # Get the user
            from app.models.user import User
            user = User.query.get(from_user_id)
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Check user balance
            if user.balance < amount:
                return {"success": False, "message": "Insufficient balance"}
            
            private_key = None
            
            # Get private key based on the available parameters
            if wallet_id and admin_id:
                # Securely decrypt the user's wallet key
                private_key = self._get_decrypted_private_key(
                    wallet_id,
                    admin_id,
                    f"Transaction: Send {amount} USDT to {to_address}"
                )
            elif admin_id:
                # Securely get admin key for admin-initiated transaction
                private_key = self._get_admin_wallet_key(
                    admin_id,
                    f"Transaction: Send {amount} USDT for user {from_user_id} to {to_address}"
                )
            elif admin_private_key:
                # Legacy support - will be deprecated
                private_key = admin_private_key
                
                # Log this less secure method for auditing
                from app.models.system_log import SystemLog
                log = SystemLog(
                    log_type='insecure_key_usage',
                    log_message=f"Transaction used plaintext private key for user {from_user_id}"
                )
                db.session.add(log)
            
                # If we have a private key, send the transaction directly
            if private_key:
                # First try Tatum.io API (primary method)
                logger.info(f"Attempting to send {amount} USDT to {to_address} using Tatum.io API")
                
                # Use Tatum service
                tx_result, error = self.tatum_service.send_usdt_transaction(
                    private_key=private_key,
                    recipient_address=to_address,
                    amount=str(amount)
                )
                
                # If Tatum transaction failed, try Web3 as fallback
                if error and WEB3_AVAILABLE:
                    logger.warning(f"Tatum API transaction failed: {error}. Trying Web3 fallback.")
                    
                    # Get sender's wallet address if needed for logging/verification
                    sender_address = None
                    if wallet_id:
                        from app.models.user_wallet import UserWallet
                        wallet = UserWallet.query.get(wallet_id)
                        if wallet:
                            sender_address = wallet.deposit_address
                    
                    # Try Web3 transaction as fallback
                    tx_result, error = self.send_usdt_via_web3(
                        private_key=private_key,
                        to_address=to_address,
                        amount=amount,
                        from_address=sender_address
                    )
                    
                    if tx_result and not error:
                        logger.info(f"Web3 fallback transaction successful: {tx_result.get('txId', '')}")
                
                if error:
                    return {"success": False, "message": error}
                
                # Deduct from user balance
                user.balance -= amount
                
                # Record the transaction
                from app.models.transaction import TatumTransaction
                
                transaction = TatumTransaction(
                    transaction_id=f"SEND-{uuid.uuid4().hex[:8]}",
                    user_id=from_user_id,
                    transaction_type='withdrawal',
                    amount=amount,
                    blockchain_tx_id=tx_result.get('txId', ''),
                    status='completed',
                    reference_id=None
                )
                
                # Log the activity
                from app.models.user_activity import UserActivity
                
                activity = UserActivity(
                    user_id=from_user_id,
                    activity_type='withdrawal',
                    activity_description=f"Sent {amount} USDT to {to_address}"
                )
                
                db.session.add(transaction)
                db.session.add(activity)
                db.session.commit()
                
                # Save transaction to MongoDB as well
                transaction.save()
                
                # Update user balance in MongoDB
                now = datetime.utcnow()
                db.users.update_one(
                    {"_id": from_user_id},
                    {"$set": {
                        "balance": user.balance,
                        "updated_at": now
                    }}
                )
                print(f"[DEBUG] Updated MongoDB user {from_user_id} balance to {user.balance} after withdrawal")
                
                return {
                    "success": True, 
                    "amount": amount, 
                    "tx_hash": tx_result.get('txId', ''),
                    "to_address": to_address
                }
            else:
                # Create a withdrawal request for admin approval
                from app.models.withdrawal import Withdrawal
                
                withdrawal = Withdrawal(
                    user_id=from_user_id,
                    amount=amount,
                    wallet_address=to_address,
                    withdrawal_status='pending'
                )
                
                # Deduct from user balance
                user.balance -= amount
                
                # Log the activity
                from app.models.user_activity import UserActivity
                
                activity = UserActivity(
                    user_id=from_user_id,
                    activity_type='withdrawal_request',
                    activity_description=f"Requested withdrawal of {amount} USDT to {to_address}"
                )
                
                db.session.add(withdrawal)
                db.session.add(activity)
                db.session.commit()
                
                return {
                    "success": True, 
                    "status": "pending", 
                    "amount": amount, 
                    "to_address": to_address,
                    "withdrawal_id": withdrawal.id
                }
            
        except Exception as e:
            db.session.rollback()
            print(f"Error sending USDT: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def distribute_daily_returns(self):
        """
        Distribute daily returns for all active investments
        
        Returns:
            Dictionary with distribution results
        """
        try:
            # Get all active investments
            from app.models.user_investments import UserInvestment
            active_investments = UserInvestment.query.filter_by(
                investment_status='active'
            ).all()
            
            if not active_investments:
                return {"success": True, "message": "No active investments found"}
            
            # Get daily return percentage from settings
            from app.services.system_service import get_system_setting
            daily_percentage = float(get_system_setting('daily_return_percentage', 23))
            daily_rate = daily_percentage / 100
            
            processed_count = 0
            completed_count = 0
            failed_count = 0
            
            for investment in active_investments:
                try:
                    # Calculate daily return
                    daily_return = investment.amount * daily_rate
                    
                    # Get user
                    from app.models.user import User
                    user = User.query.get(investment.user_id)
                    
                    if not user:
                        print(f"User not found for investment {investment.id}")
                        failed_count += 1
                        continue
                    
                    # Add return to user balance
                    user.balance += daily_return
                    
                    # Record earnings
                    from app.models.user_earnings import UserEarnings
                    
                    earnings = UserEarnings(
                        user_id=user.id,
                        source_id=investment.id,
                        amount=daily_return,
                        earning_type='daily',
                        earning_status='processed'
                    )
                    
                    # Record transaction
                    from app.models.transaction import TatumTransaction
                    
                    transaction = TatumTransaction(
                        transaction_id=f"DAILY-{uuid.uuid4().hex[:8]}",
                        user_id=user.id,
                        transaction_type='earning',
                        amount=daily_return,
                        status='completed',
                        reference_id=str(investment.id)
                    )
                    
                    db.session.add(earnings)
                    db.session.add(transaction)
                    processed_count += 1
                    
                    # Save transaction to MongoDB as well
                    transaction.save()
                    
                    # Update user balance in MongoDB
                    now = datetime.utcnow()
                    db.users.update_one(
                        {"_id": user.id},
                        {"$set": {
                            "balance": user.balance,
                            "updated_at": now
                        }}
                    )
                    print(f"[DEBUG] Updated MongoDB user {user.id} balance to {user.balance} after daily return")
                    
                    # Check if investment is complete
                    from datetime import datetime, timedelta
                    investment_days = int(get_system_setting('investment_days', 5))
                    
                    if (datetime.utcnow() - investment.activation_date).days >= investment_days:
                        investment.investment_status = 'completed'
                        investment.completion_date = datetime.utcnow()
                        
                        # Record activity
                        from app.models.user_activity import UserActivity
                        
                        activity = UserActivity(
                            user_id=user.id,
                            activity_type='investment_completed',
                            activity_description=f"Investment of {investment.amount} USDT completed with total returns."
                        )
                        
                        db.session.add(activity)
                        completed_count += 1
                        
                except Exception as e:
                    print(f"Error processing investment {investment.id}: {str(e)}")
                    failed_count += 1
                    continue
            
            db.session.commit()
            
            return {
                "success": True,
                "processed": processed_count,
                "completed": completed_count,
                "failed": failed_count
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"Error distributing daily returns: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def process_deposit(self, user_id, amount, tx_hash):
        """
        Process a USDT deposit for a user and apply referral commissions
        
        Args:
            user_id: User ID 
            amount: Deposit amount
            tx_hash: Transaction hash
            
        Returns:
            Dictionary with deposit results
        """
        try:
            # Get user
            from app.models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Add amount to user balance
            user.balance += amount
            
            # Record deposit transaction
            from app.models.transaction import TatumTransaction
            
            tx = TatumTransaction(
                transaction_id=f"DEP-{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                transaction_type='deposit',
                amount=amount,
                blockchain_tx_id=tx_hash,
                status='completed'
            )
            
            # Record activity
            from app.models.user_activity import UserActivity
            
            activity = UserActivity(
                user_id=user_id,
                activity_type='deposit',
                activity_description=f"Deposited {amount} USDT"
            )
            
            db.session.add(tx)
            db.session.add(activity)
            
            # Process referral commissions if applicable
            self._process_referral_tree_commissions(user_id, amount)
            
            # Process pending investments
            self._process_pending_investments(user_id)
            
            db.session.commit()
            
            # Save transaction to MongoDB as well
            tx.save()
            
            # Update user balance in MongoDB
            now = datetime.utcnow()
            db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "balance": user.balance,
                    "updated_at": now
                }}
            )
            print(f"[DEBUG] Updated MongoDB user {user_id} balance to {user.balance} after deposit")
            
            return {"success": True, "amount": amount, "user_id": user_id}
            
        except Exception as e:
            db.session.rollback()
            print(f"Error processing deposit: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def _process_referral_tree_commissions(self, user_id, amount):
        """
        Process commissions for the entire referral tree
        
        Args:
            user_id: User ID that made the deposit
            amount: Deposit amount
        """
        try:
            # Get referral tree
            from app.models.referral_tree import ReferralTree
            referral = ReferralTree.query.filter_by(user_id=user_id).first()
            
            if not referral or not referral.referrer_id:
                return  # No referrer
            
            # Get commission percentages from investment plans
            from app.models.investment_plan import InvestmentPlan
            plans = InvestmentPlan.query.all()
            
            # Create a dictionary of level -> percentage
            commission_rates = {plan.plan_level: plan.daily_percentage for plan in plans}
            
            # Total referral percentage to distribute
            from app.services.system_service import get_system_setting
            total_referral_percentage = float(get_system_setting('referral_fee_percentage', 5))
            
            # Process referral chain up to 12 levels deep
            current_referrer_id = referral.referrer_id
            level = 1
            
            while current_referrer_id and level <= 12:
                # Get referrer
                from app.models.user import User
                referrer = User.query.get(current_referrer_id)
                
                if not referrer:
                    break
                
                # Calculate commission amount
                commission_rate = commission_rates.get(level, 0) * (total_referral_percentage / 100)
                commission_amount = amount * commission_rate
                
                if commission_amount > 0:
                    # Check eligibility
                    eligible = self._check_referrer_eligibility(current_referrer_id)
                    
                    if eligible:
                        # Add commission to referrer balance and record
                        self.process_referral_commission(
                            user_id=current_referrer_id,
                            amount=commission_amount,
                            source_user_id=user_id
                        )
                    else:
                        # Record as pending
                        from app.models.user_earnings import UserEarnings
                        
                        earnings = UserEarnings(
                            user_id=current_referrer_id,
                            source_id=user_id,
                            amount=commission_amount,
                            earning_type='referral',
                            earning_level=level,
                            earning_status='pending'
                        )
                        
                        db.session.add(earnings)
                
                # Move up the tree
                referral = ReferralTree.query.filter_by(user_id=current_referrer_id).first()
                if not referral:
                    break
                    
                current_referrer_id = referral.referrer_id
                level += 1
                
        except Exception as e:
            print(f"Error processing referral tree commissions: {str(e)}")
            raise
    
    def _check_referrer_eligibility(self, user_id):
        """
        Check if a referrer is eligible to receive commissions
        
        Args:
            user_id: User ID to check
            
        Returns:
            Boolean indicating eligibility
        """
        try:
            # Check income hold status
            from app.models.income_hold_status import IncomeHoldStatus
            hold_status = IncomeHoldStatus.query.filter_by(user_id=user_id).first()
            
            if hold_status and hold_status.level_income_on_hold:
                return False
            
            # Check active legs
            from app.models.user_legs import UserLegs
            legs = UserLegs.query.filter_by(user_id=user_id).first()
            
            # Get minimum required legs from settings
            from app.services.system_service import get_system_setting
            min_legs = int(get_system_setting('min_legs_for_reward', 5))
            
            if not legs or legs.active_legs < min_legs:
                return False
            
            # Check active investments
            from app.models.user_investments import UserInvestment
            active_investments = UserInvestment.query.filter_by(
                user_id=user_id,
                investment_status='active'
            ).count()
            
            return active_investments > 0
            
        except Exception as e:
            print(f"Error checking referrer eligibility: {str(e)}")
            return False
    
    def _process_pending_investments(self, user_id):
        """
        Process any pending investments for a user
        
        Args:
            user_id: User ID
        """
        try:
            # Get user
            from app.models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return
            
            # Get pending investments
            from app.models.user_investments import UserInvestment
            pending_investments = UserInvestment.query.filter_by(
                user_id=user_id,
                investment_status='pending'
            ).all()
            
            if not pending_investments:
                return
            
            # Process each pending investment
            for investment in pending_investments:
                if user.balance >= investment.amount:
                    # Deduct from balance
                    user.balance -= investment.amount
                    
                    # Activate investment
                    investment.investment_status = 'active'
                    investment.activation_date = datetime.utcnow()
                    
                    # Calculate completion date
                    from app.services.system_service import get_system_setting
                    investment_days = int(get_system_setting('investment_days', 5))
                    
                    from datetime import timedelta
                    investment.completion_date = investment.activation_date + timedelta(days=investment_days)
                    
                    # Record activity
                    from app.models.user_activity import UserActivity
                    
                    activity = UserActivity(
                        user_id=user_id,
                        activity_type='investment_activated',
                        activity_description=f"Investment of {investment.amount} USDT activated"
                    )
                    
                    db.session.add(activity)
                    
                    # Update user cycle information
                    self._update_user_cycle(user_id, investment.amount)
            
        except Exception as e:
            print(f"Error processing pending investments: {str(e)}")
            raise
    
    def _update_user_cycle(self, user_id, investment_amount):
        """
        Update user cycle information based on investment
        
        Args:
            user_id: User ID
            investment_amount: Investment amount
        """
        try:
            # Get or create user cycle
            from app.models.user_cycles import UserCycle
            
            # Check for active cycle
            active_cycle = UserCycle.query.filter_by(
                user_id=user_id,
                cycle_status='active'
            ).first()
            
            if active_cycle:
                # Update existing cycle
                active_cycle.total_units_bought += 1
                active_cycle.cycle_amount += investment_amount
            else:
                # Get previous cycle to determine next cycle number
                previous_cycle = UserCycle.query.filter_by(
                    user_id=user_id
                ).order_by(UserCycle.cycle_number.desc()).first()
                
                cycle_number = 1
                if previous_cycle:
                    cycle_number = previous_cycle.cycle_number + 1
                
                # Get units allowed for this cycle
                from app.models.unit_progression import UnitProgression
                progression = UnitProgression.query.filter_by(
                    cycle_number=cycle_number-1  # Cycles are 1-indexed, table is 0-indexed
                ).first()
                
                total_units_allowed = 1
                if progression:
                    total_units_allowed = progression.units_allowed
                
                # Create new cycle
                new_cycle = UserCycle(
                    user_id=user_id,
                    cycle_number=cycle_number,
                    start_date=datetime.utcnow(),
                    total_units_allowed=total_units_allowed,
                    total_units_bought=1,
                    cycle_amount=investment_amount,
                    cycle_status='active'
                )
                
                db.session.add(new_cycle)
                
                # Update income hold status
                self._update_income_hold_status(user_id, 1)
        
        except Exception as e:
            print(f"Error updating user cycle: {str(e)}")
            raise
    
    def _update_income_hold_status(self, user_id, current_units):
        """
        Update income hold status based on user's investment pattern
        
        Args:
            user_id: User ID
            current_units: Current cycle units
        """
        try:
            # Get or create hold status
            from app.models.income_hold_status import IncomeHoldStatus
            hold_status = IncomeHoldStatus.query.filter_by(user_id=user_id).first()
            
            if not hold_status:
                # Create new record
                hold_status = IncomeHoldStatus(
                    user_id=user_id,
                    level_income_on_hold=False,
                    team_rewards_on_hold=False,
                    initial_unit_count=current_units,
                    last_purchase_date=datetime.utcnow()
                )
                db.session.add(hold_status)
            else:
                # Check if need to activate hold
                if current_units < hold_status.initial_unit_count:
                    # Put income on hold
                    hold_status.level_income_on_hold = True
                    hold_status.team_rewards_on_hold = True
                    
                    # Log activity
                    from app.models.user_activity import UserActivity
                    
                    activity = UserActivity(
                        user_id=user_id,
                        activity_type='income_hold',
                        activity_description=f"Income put on hold due to decreased unit count (from {hold_status.initial_unit_count} to {current_units})"
                    )
                    
                    db.session.add(activity)
                else:
                    # If sufficient units, release hold
                    if hold_status.level_income_on_hold or hold_status.team_rewards_on_hold:
                        hold_status.level_income_on_hold = False
                        hold_status.team_rewards_on_hold = False
                        
                        # Log activity
                        from app.models.user_activity import UserActivity
                        
                        activity = UserActivity(
                            user_id=user_id,
                            activity_type='income_released',
                            activity_description=f"Income hold released due to sufficient unit count ({current_units})"
                        )
                        
                        db.session.add(activity)
                        
                        # Process pending earnings
                        self._process_pending_earnings(user_id)
                
                # Update unit count and purchase date
                hold_status.initial_unit_count = max(current_units, hold_status.initial_unit_count)
                hold_status.last_purchase_date = datetime.utcnow()
                
        except Exception as e:
            print(f"Error updating income hold status: {str(e)}")
            raise
    
    def _process_pending_earnings(self, user_id):
        """
        Process pending earnings for a user once income hold is released
        
        Args:
            user_id: User ID
        """
        try:
            # Get pending earnings
            from app.models.user_earnings import UserEarnings
            pending_earnings = UserEarnings.query.filter_by(
                user_id=user_id,
                earning_status='pending'
            ).all()
            
            if not pending_earnings:
                return
            
            # Get user
            from app.models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return
            
            # Process each pending earning
            for earning in pending_earnings:
                # Add to user balance
                user.balance += earning.amount
                
                # Update status
                earning.earning_status = 'processed'
                earning.processed_at = datetime.utcnow()
                
                # Record transaction
                from app.models.transaction import TatumTransaction
                
                tx_type = 'commission' if earning.earning_type == 'referral' else earning.earning_type
                
                tx = TatumTransaction(
                    transaction_id=f"RELEASE-{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    transaction_type=tx_type,
                    amount=earning.amount,
                    status='completed',
                    reference_id=str(earning.source_id) if earning.source_id else None
                )
                
                db.session.add(tx)
                
                # Save transaction to MongoDB as well
                tx.save()
            
            # Update MongoDB balance after all pending earnings are processed
            now = datetime.utcnow()
            db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "balance": user.balance,
                    "updated_at": now
                }}
            )
            print(f"[DEBUG] Updated MongoDB user {user_id} balance to {user.balance} after releasing pending earnings")
            
            # Log activity
            from app.models.user_activity import UserActivity
            
            activity = UserActivity(
                user_id=user_id,
                activity_type='earnings_processed',
                activity_description=f"Processed {len(pending_earnings)} pending earnings"
            )
            
            db.session.add(activity)
            
        except Exception as e:
            print(f"Error processing pending earnings: {str(e)}")
            raise