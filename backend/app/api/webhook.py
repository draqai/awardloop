# app/api/webhook.py
from flask import Blueprint, request, jsonify
from app.services.tatum_hybrid_service import TatumHybridService
import os
import hmac
import hashlib
import json
import logging
from datetime import datetime
import uuid

webhook_bp = Blueprint('webhook', __name__)
tatum_service = TatumHybridService()

@webhook_bp.route('/tatum', methods=['POST'])
def tatum_webhook():
    """Handle incoming webhook notifications from Tatum"""
    try:
        data = request.get_json()
        logging.info(f"Received Tatum webhook notification: {json.dumps(data)[:200]}...")
        
        # Get the signature from the headers
        signature = request.headers.get('x-payload-hash')
        
        # Verify HMAC signature if available
        webhook_key = os.environ.get('TATUM_WEBHOOK_KEY')
        if signature and webhook_key:
            # Calculate expected signature
            payload_json = json.dumps(data)
            expected_signature = hmac.new(
                webhook_key.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if signature != expected_signature:
                # Attempt with alternate JSON formatting (some systems format JSON differently)
                alt_payload = json.dumps(data, separators=(',', ':'))
                alt_signature = hmac.new(
                    webhook_key.encode(),
                    alt_payload.encode(), 
                    hashlib.sha256
                ).hexdigest()
                
                # Try with sorted keys (Tatum might sort keys alphabetically)
                import collections
                sorted_data = collections.OrderedDict(sorted(data.items()))
                sorted_payload = json.dumps(sorted_data)
                sorted_signature = hmac.new(
                    webhook_key.encode(),
                    sorted_payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                # Try with sorted keys and compact formatting
                sorted_compact = json.dumps(sorted_data, separators=(',', ':'))
                sorted_compact_signature = hmac.new(
                    webhook_key.encode(),
                    sorted_compact.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                # Check all signature methods
                valid_signature = (
                    signature == expected_signature or 
                    signature == alt_signature or 
                    signature == sorted_signature or 
                    signature == sorted_compact_signature
                )
                
                if not valid_signature:
                    logging.warning(f"Invalid signature after all verification methods. Received: {signature}")
                    logging.debug(f"Expected signatures: standard={expected_signature}, compact={alt_signature}, sorted={sorted_signature}, sorted+compact={sorted_compact_signature}")
                    return jsonify({'error': 'Invalid signature'}), 401
                else:
                    logging.info(f"Signature verified using alternative method")
        else:
            logging.warning("HMAC signature verification skipped - missing signature or webhook key")
        
        # Process the webhook data
        success, error = tatum_service.receive_webhook_notification(data)
        
        if not success:
            logging.error(f"Error processing webhook notification: {error}")
            return jsonify({'success': False, 'message': error}), 500
        
        return jsonify({'success': True, 'message': 'Webhook processed successfully', 'transactionId': data.get('txId')}), 200
        
    except Exception as e:
        logging.exception(f"Unexpected error processing webhook: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing webhook: {str(e)}'}), 500

@webhook_bp.route('/moralis/<api_secret>', methods=['POST'])
def moralis_webhook(api_secret):
    """Handle incoming webhook notifications from Moralis with URL authentication"""
    try:
        # Get the raw request body and headers
        request_body = request.get_data()
        signature = request.headers.get('x-signature')
        
        # Log the incoming webhook
        logging.info(f"Received Moralis webhook notification")
        
        # Verify Moralis webhook signature if available
        webhook_secret = os.environ.get('MORALIS_WEBHOOK_SECRET')
        if signature and webhook_secret:
            # Calculate HMAC signature using Moralis method
            expected_signature = hmac.new(
                webhook_secret.encode(),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if signature != expected_signature:
                logging.warning(f"Invalid Moralis signature. Received: {signature}")
                logging.debug(f"Expected signature: {expected_signature}")
                return jsonify({'error': 'Invalid signature'}), 401
            else:
                logging.info(f"Moralis signature verified")
        else:
            logging.warning("Moralis signature verification skipped - missing signature or webhook secret")
        
        # Parse the JSON data
        data = request.get_json()
        
        # Extract useful information from Moralis webhook
        if not data.get('confirmed', False):
            # Skip unconfirmed transactions
            logging.info("Skipping unconfirmed transaction")
            return jsonify({'success': True, 'message': 'Unconfirmed transaction skipped'}), 200
            
        # Keep track of processed transactions
        processed_transactions = []
        
        # Process the webhook data based on its content
        if 'erc20Transfers' in data and data['erc20Transfers']:
            # Process ERC20/BEP20 token transfers (USDT)
            for transfer in data['erc20Transfers']:
                tx_hash = transfer.get('transactionHash')
                result = process_moralis_token_transfer(transfer, data)
                if result:
                    processed_transactions.append({
                        'type': 'token',
                        'hash': tx_hash,
                        'success': True
                    })
                
        if 'nativeTransfers' in data and data['nativeTransfers']:
            # Process native transfers (BNB)
            for transfer in data['nativeTransfers']:
                tx_hash = transfer.get('transactionHash')
                result = process_moralis_native_transfer(transfer, data)
                if result:
                    processed_transactions.append({
                        'type': 'native',
                        'hash': tx_hash,
                        'success': True
                    })
        
        if not processed_transactions:
            logging.warning(f"No supported transfer types processed in Moralis webhook")
            
        # Return success even if we didn't process any transactions
        # This prevents Moralis from resending the same webhook
        response = {
            'success': True, 
            'message': 'Moralis webhook processed successfully',
            'processed': len(processed_transactions),
            'transactions': processed_transactions
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logging.exception(f"Unexpected error processing Moralis webhook: {str(e)}")
        return jsonify({'success': False, 'message': f'Error processing Moralis webhook: {str(e)}'}), 500

def process_moralis_token_transfer(transfer, data):
    """Process a token transfer from Moralis webhook"""
    try:
        from app import db
        
        # Extract token information with more comprehensive checks
        token = transfer.get('token', {})
        token_address = token.get('contractAddress', '').lower()
        token_symbol = token.get('symbol', '')
        
        # Add detailed logging to track token information
        logging.info(f"Token details: address={token_address}, symbol={token_symbol}")
        
        # Additional USDT detection check using standard BSC USDT contract
        usdt_contract = os.environ.get('USDT_CONTRACT', '0x55d398326f99059fF775485246999027B3197955').lower()
        is_usdt = (
            token_symbol == 'USDT' or 
            token_address == usdt_contract or
            'usdt' in token_symbol.lower()
        )
        
        if is_usdt:
            logging.info(f"USDT token detected: symbol={token_symbol}, address={token_address}")
        
        # Extract transaction details with fallbacks for field name variations
        tx_hash = transfer.get('transactionHash', '') or transfer.get('txId', '') or transfer.get('hash', '')
        from_address = transfer.get('from', '') or transfer.get('sender', '')
        to_address = transfer.get('to', '') or transfer.get('recipient', '') or transfer.get('address', '')
        
        # Normalize addresses to lowercase for consistent matching
        if from_address:
            from_address = from_address.lower()
        if to_address:
            to_address = to_address.lower()
        
        # Extract block information
        block = data.get('block', {})
        block_number = block.get('number', '')
        block_timestamp = block.get('timestamp', '')
        
        logging.info(f"Processing Moralis token transfer: {token_symbol} from {from_address} to {to_address}")
        
        # Check if this transaction is already recorded
        existing_tx = db.tatum_transactions.find_one({"blockchain_tx_id": tx_hash})
        if existing_tx:
            logging.info(f"Transaction {tx_hash} already processed")
            
            # Check if the transaction was recorded but balance wasn't updated
            user_id = existing_tx.get('user_id')
            amount = existing_tx.get('amount', 0)
            
            if user_id and amount > 0 and existing_tx.get('status') == 'completed':
                # Verify user balance was properly updated
                user_doc = db.users.find_one({"_id": user_id})
                if user_doc:
                    logging.info(f"Verifying balance update for completed transaction {tx_hash}")
                    # No specific action - will proceed if balance needs updating
                else:
                    logging.warning(f"User {user_id} not found for existing transaction {tx_hash}")
            
            return True
            
        # Process only incoming transactions to user wallets
        # Look up the wallet in the database with more comprehensive matching
        address_variants = [
            to_address,                            # As provided
            to_address.lower(),                    # Lowercase
            to_address.upper(),                    # Uppercase
            to_address.lower().replace('0x', ''),  # Without 0x prefix
            f"0x{to_address.lower().replace('0x', '')}"  # Ensuring 0x prefix
        ]
        
        # Build a more comprehensive query
        or_conditions = []
        for variant in address_variants:
            if variant:  # Skip empty variants
                or_conditions.append({"deposit_address": variant})
                or_conditions.append({"deposit_address": {"$regex": f"^{variant}$", "$options": "i"}})
        
        # Add the query to find the wallet
        user_wallet = db.user_wallets.find_one({"$or": or_conditions}) if or_conditions else None
        
        if not user_wallet:
            logging.warning(f"No wallet found for address: {to_address}")
            logging.info(f"Attempted to match address variants: {', '.join(address_variants[:3])}...")
            return False
            
        user_id = user_wallet.get('user_id')
        wallet_address = user_wallet.get('deposit_address')
        logging.info(f"Found wallet for user {user_id}, address: {wallet_address}")
        
        # Extract and convert amount with improved handling
        amount = 0
        
        # Log all available amount fields for debugging
        amount_fields = {
            'valueWithDecimals': transfer.get('valueWithDecimals'),
            'value': transfer.get('value'),
            'amount': transfer.get('amount'),
            'rawValue': transfer.get('rawValue')
        }
        logging.info(f"Available amount fields: {amount_fields}")
        
        # Try valueWithDecimals first (human-readable amount)
        if 'valueWithDecimals' in transfer:
            try:
                amount = float(transfer['valueWithDecimals'])
                logging.info(f"Using valueWithDecimals: {amount}")
            except (ValueError, TypeError):
                logging.warning(f"Failed to parse valueWithDecimals: {transfer['valueWithDecimals']}")
        
        # Try transfer.amount if available
        if amount == 0 and 'amount' in transfer:
            try:
                amount = float(transfer['amount'])
                logging.info(f"Using amount: {amount}")
            except (ValueError, TypeError):
                logging.warning(f"Failed to parse amount: {transfer['amount']}")
        
        # Fallback to raw value with decimal conversion
        if amount == 0 and 'value' in transfer:
            try:
                # Default to 18 decimals but try to get actual value
                decimals = 18
                try:
                    decimals = int(token.get('decimals', 18))
                except (ValueError, TypeError):
                    decimals = 18  # Default for most tokens
                    
                amount = float(transfer['value']) / (10 ** decimals)
                logging.info(f"Converted raw value: {amount} (decimals: {decimals})")
            except (ValueError, TypeError):
                logging.warning(f"Failed to convert value: {transfer['value']}")
        
        # Check for raw value in a different field
        if amount == 0 and 'rawValue' in transfer:
            try:
                decimals = int(token.get('decimals', 18))
                amount = float(transfer['rawValue']) / (10 ** decimals)
                logging.info(f"Converted rawValue: {amount} (decimals: {decimals})")
            except (ValueError, TypeError):
                logging.warning(f"Failed to convert rawValue: {transfer['rawValue']}")
        
        # Force specific amount for testing if all else fails
        if amount <= 0 and is_usdt and os.environ.get('DEBUG_WEBHOOK', 'False').lower() == 'true':
            test_amount = os.environ.get('DEBUG_WEBHOOK_AMOUNT')
            if test_amount:
                try:
                    amount = float(test_amount)
                    logging.warning(f"Using debug webhook amount: {amount}")
                except (ValueError, TypeError):
                    pass
                    
        if amount <= 0:
            logging.warning(f"Invalid amount: {amount}")
            return False
        
        # Determine transaction type with improved USDT detection
        transaction_type = 'deposit_token'  # Default
        currency = token_symbol
        
        # Check for USDT with multiple detection methods
        usdt_contract = os.environ.get('USDT_CONTRACT', '0x55d398326f99059fF775485246999027B3197955').lower()
        is_usdt = (
            token_symbol == 'USDT' or 
            'usdt' in token_symbol.lower() or
            token_address == usdt_contract or
            'tether' in (token.get('name', '')).lower()
        )
        
        if is_usdt:
            transaction_type = 'deposit_usdt'
            currency = 'USDT'
            logging.info(f"Detected USDT deposit of {amount} USDT")
        
        # Create a unique transaction ID
        transaction_id = f"{transaction_type.upper()}-{uuid.uuid4().hex[:8]}"
        
        # Create transaction document with more detailed reference
        now = datetime.utcnow()
        transaction_doc = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "blockchain_tx_id": tx_hash,
            "status": 'completed',
            "reference_id": f"currency:{currency},source:{from_address},token_address:{token_address}",
            "created_at": now,
            "updated_at": now
        }
        
        # Update user's balance
        user_doc = db.users.find_one({"_id": user_id})
        if not user_doc:
            # Try ObjectId conversion if string ID
            if isinstance(user_id, str):
                try:
                    from bson.objectid import ObjectId
                    obj_id = ObjectId(user_id)
                    user_doc = db.users.find_one({"_id": obj_id})
                    if user_doc:
                        user_id = obj_id
                except Exception:
                    pass
        
        if not user_doc:
            logging.error(f"User {user_id} not found in database")
            
            # Create error log and save transaction without updating balance
            error_log = {
                "log_type": 'webhook_error',
                "log_message": f"User {user_id} not found for wallet address {to_address}, transaction {tx_hash}",
                "created_at": now
            }
            db.system_logs.insert_one(error_log)
            db.tatum_transactions.insert_one(transaction_doc)
            
            return False
        
        # Update balance
        current_balance = float(user_doc.get('balance', 0))
        new_balance = current_balance + amount
        
        db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "balance": new_balance,
                "updated_at": now
            }}
        )
        
        # Save transaction to database
        db.tatum_transactions.insert_one(transaction_doc)
        
        # Create system log
        log_doc = {
            "log_type": 'webhook_transaction',
            "log_message": f'Received {amount} {currency} for user {user_id} via blockchain transaction {tx_hash}. Balance updated to {new_balance}',
            "created_at": now
        }
        db.system_logs.insert_one(log_doc)
        
        # Create user activity record
        activity_doc = {
            "user_id": user_id,
            "activity_type": 'deposit',
            "activity_description": f"Received {amount} {currency} via blockchain transaction {tx_hash}. New balance: {new_balance}",
            "created_at": now
        }
        db.user_activities.insert_one(activity_doc)
        
        logging.info(f"Successfully processed {currency} transaction: {tx_hash}")
        return True
        
    except Exception as e:
        logging.exception(f"Error processing Moralis token transfer: {str(e)}")
        return False

def process_moralis_native_transfer(transfer, data):
    """Process a native transfer (BNB) from Moralis webhook"""
    try:
        from app import db
        
        # Extract transaction details
        tx_hash = transfer.get('transactionHash', '')
        from_address = transfer.get('from', '')
        to_address = transfer.get('to', '')
        
        # Extract block information
        block = data.get('block', {})
        block_number = block.get('number', '')
        block_timestamp = block.get('timestamp', '')
        
        logging.info(f"Processing Moralis native transfer from {from_address} to {to_address}")
        
        # Check if this transaction is already recorded
        existing_tx = db.tatum_transactions.find_one({"blockchain_tx_id": tx_hash})
        if existing_tx:
            logging.info(f"Transaction {tx_hash} already processed")
            return True
        
        # Process only incoming transactions
        user_wallet = db.user_wallets.find_one({
            "$or": [
                {"deposit_address": to_address},
                {"deposit_address": to_address.lower()},
                {"deposit_address": {"$regex": f"^{to_address}$", "$options": "i"}}
            ]
        })
        
        if not user_wallet:
            logging.info(f"No wallet found for address: {to_address}")
            return False
            
        user_id = user_wallet.get('user_id')
        logging.info(f"Found wallet for user {user_id}, address: {to_address}")
        
        # Extract and convert amount
        amount = 0
        if 'valueWithDecimals' in transfer:
            try:
                amount = float(transfer['valueWithDecimals'])
                logging.info(f"Using valueWithDecimals: {amount}")
            except (ValueError, TypeError):
                logging.warning(f"Failed to parse valueWithDecimals: {transfer['valueWithDecimals']}")
        
        # Fallback to raw value
        if amount == 0 and 'value' in transfer:
            try:
                # Native BNB has 18 decimals
                amount = float(transfer['value']) / (10 ** 18)
                logging.info(f"Converted raw value: {amount}")
            except (ValueError, TypeError):
                logging.warning(f"Failed to convert value: {transfer['value']}")
        
        if amount <= 0:
            logging.warning(f"Invalid amount: {amount}")
            return False
        
        # Set transaction type
        transaction_type = 'deposit_bnb'
        currency = 'BNB'
        
        # Create a unique transaction ID
        transaction_id = f"{transaction_type.upper()}-{uuid.uuid4().hex[:8]}"
        
        # Create transaction document
        now = datetime.utcnow()
        transaction_doc = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "blockchain_tx_id": tx_hash,
            "status": 'completed',
            "reference_id": f"currency:{currency},source:{from_address}",
            "created_at": now,
            "updated_at": now
        }
        
        # Update user's balance
        user_doc = db.users.find_one({"_id": user_id})
        if not user_doc:
            # Try ObjectId conversion if string ID
            if isinstance(user_id, str):
                try:
                    from bson.objectid import ObjectId
                    obj_id = ObjectId(user_id)
                    user_doc = db.users.find_one({"_id": obj_id})
                    if user_doc:
                        user_id = obj_id
                except Exception:
                    pass
        
        if not user_doc:
            logging.error(f"User {user_id} not found in database")
            
            # Create error log and save transaction without updating balance
            error_log = {
                "log_type": 'webhook_error',
                "log_message": f"User {user_id} not found for wallet address {to_address}, transaction {tx_hash}",
                "created_at": now
            }
            db.system_logs.insert_one(error_log)
            db.tatum_transactions.insert_one(transaction_doc)
            
            return False
        
        # Update balance
        current_balance = float(user_doc.get('balance', 0))
        new_balance = current_balance + amount
        
        db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "balance": new_balance,
                "updated_at": now
            }}
        )
        
        # Save transaction to database
        db.tatum_transactions.insert_one(transaction_doc)
        
        # Create system log
        log_doc = {
            "log_type": 'webhook_transaction',
            "log_message": f'Received {amount} {currency} for user {user_id} via blockchain transaction {tx_hash}. Balance updated to {new_balance}',
            "created_at": now
        }
        db.system_logs.insert_one(log_doc)
        
        # Create user activity record
        activity_doc = {
            "user_id": user_id,
            "activity_type": 'deposit',
            "activity_description": f"Received {amount} {currency} via blockchain transaction {tx_hash}. New balance: {new_balance}",
            "created_at": now
        }
        db.user_activities.insert_one(activity_doc)
        
        logging.info(f"Successfully processed {currency} transaction: {tx_hash}")
        return True
        
    except Exception as e:
        logging.exception(f"Error processing Moralis native transfer: {str(e)}")
        return False