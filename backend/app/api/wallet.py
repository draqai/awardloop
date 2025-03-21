# app/api/wallet.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.tatum_hybrid_service import TatumHybridService
from app import db, socketio
from functools import wraps
from datetime import datetime
import uuid

wallet_bp = Blueprint('wallet', __name__)
tatum_service = TatumHybridService()

def get_user_id_from_jwt():
    """
    Helper function to extract user ID from JWT identity regardless of format
    Handles both string IDs and dictionary format {'id': user_id}
    """
    identity = get_jwt_identity()
    if isinstance(identity, dict) and 'id' in identity:
        return identity['id']
    return identity  # Assume the identity itself is the user ID

def admin_required(f):
    """Decorator to require admin role for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user ID from JWT token
        current_user_id = get_user_id_from_jwt()
        
        # Try to convert to ObjectId if it's a string
        if isinstance(current_user_id, str):
            try:
                from bson.objectid import ObjectId
                current_user_id = ObjectId(current_user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
                
        # Check if user is admin using MongoDB
        user_doc = db.users.find_one({"_id": current_user_id})
        
        if not user_doc or not user_doc.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

@wallet_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_wallet():
    """Generate a new wallet for the current user"""
    try:
        # Get user ID from JWT token
        current_user_id = get_user_id_from_jwt()
        
        # Try to convert to ObjectId if it's a string
        if isinstance(current_user_id, str):
            try:
                from bson.objectid import ObjectId
                current_user_id = ObjectId(current_user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
        
        # Check if user already has wallets using MongoDB
        existing_wallets = list(db.user_wallets.find({"user_id": current_user_id}))
        
        # Prevent duplicate wallet creation - users should only have one wallet
        if len(existing_wallets) > 0:
            # User already has at least one wallet, return the most recently created one
            latest_wallet = max(existing_wallets, key=lambda w: w.get('created_at', datetime.utcnow()))
            return jsonify({
                'success': True,
                'message': 'Existing wallet found',
                'wallet': {
                    'address': latest_wallet.get('deposit_address', ''),
                    'qr_code_url': tatum_service.get_qr_code_url(latest_wallet.get('deposit_address', ''))
                }
            }), 200
        
        # Generate a new wallet
        wallet, error = tatum_service.generate_wallet(current_user_id)
        
        if error:
            return jsonify({'success': False, 'message': error}), 500
        
        # Emit Socket.IO event for wallet generation
        socketio.emit('wallet_generated', {
            'user_id': str(current_user_id),
            'address': wallet.deposit_address,
            'timestamp': datetime.utcnow().isoformat()
        }, room=str(current_user_id))
        
        return jsonify({
            'success': True,
            'message': 'Wallet generated successfully',
            'wallet': {
                'address': wallet.deposit_address,
                'qr_code_url': tatum_service.get_qr_code_url(wallet.deposit_address)
            }
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@wallet_bp.route('/admin/transfer-to-admin', methods=['POST'])
@jwt_required()
@admin_required
def transfer_to_admin_wallet():
    """Transfer all USDT from a user's wallet to admin wallet"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        admin_wallet_address = data.get('admin_wallet_address') # Optional override
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        # Get admin ID from JWT token for audit purposes
        admin_id = get_user_id_from_jwt()
        
        # Try to convert user_id to ObjectId if it's a string
        if isinstance(user_id, str):
            try:
                from bson.objectid import ObjectId
                user_id = ObjectId(user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
        
        # Execute the transfer
        result = tatum_service.transfer_to_admin(
            user_id=user_id,
            admin_id=admin_id,
            admin_wallet_address=admin_wallet_address
        )
        
        if not result.get('success'):
            return jsonify(result), 400
        
        # Emit Socket.IO events for real-time updates
        if result.get('success'):
            # Create a transaction ID for the socket event
            transaction_id = f"ADMIN-TRANSFER-{result.get('tx_hash', '')[-8:]}"
            timestamp = datetime.utcnow().isoformat()
            
            # Emit transaction event
            socketio.emit('new_deposit', {
                "transaction_id": transaction_id,
                "user_id": str(user_id),
                "amount": float(result.get('amount', 0)),
                "tx_hash": result.get('tx_hash', ''),
                "wallet_address": result.get('from_address', ''),
                "timestamp": timestamp,
                "transaction_type": 'admin_transfer'
            }, broadcast=True)
            
            # Emit balance update event
            user_doc = db.users.find_one({"_id": user_id})
            current_balance = user_doc.get('balance', 0) if user_doc else 0
            
            socketio.emit('balance_updated', {
                "user_id": str(user_id),
                "balance": current_balance,
                "transaction_id": transaction_id,
                "timestamp": timestamp
            }, room=str(user_id))
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@wallet_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    """Get the balance for the current user's wallet"""
    try:
        # Get user ID from JWT token
        current_user_id = get_user_id_from_jwt()
        
        # Try to convert to ObjectId if it's a string
        if isinstance(current_user_id, str):
            try:
                from bson.objectid import ObjectId
                current_user_id = ObjectId(current_user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
                
        # Get user's database balance from MongoDB
        user_doc = db.users.find_one({"_id": current_user_id})
        
        if not user_doc:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Get user's database balance (which reflects purchases and withdrawals)
        database_balance = float(user_doc.get('balance', 0.0)) if user_doc else 0.0
        
        # Find wallets with non-empty deposit address using MongoDB
        wallet_docs_with_address = list(
            db.user_wallets.find({
                "user_id": current_user_id,
                "deposit_address": {"$ne": None, "$ne": ""}
            }).sort("created_at", -1)
        )
        
        # If no wallet with address found, fall back to the most recent wallet
        wallet_doc = None
        if wallet_docs_with_address:
            wallet_doc = wallet_docs_with_address[0]
        else:
            all_wallet_docs = list(
                db.user_wallets.find({"user_id": current_user_id}).sort("created_at", -1)
            )
            if all_wallet_docs:
                wallet_doc = all_wallet_docs[0]
        
        if not wallet_doc:
            return jsonify({'success': False, 'message': 'No wallet found for this user'}), 404
        
        # Get blockchain balance for reference (not displayed)
        blockchain_balance = tatum_service.get_balance(wallet_doc.get('deposit_address', ''))
        
        # Get blockchain BNB balance from the user's actual wallet
        # Default to zero if not retrievable
        bnb_balance = 0.0
        if blockchain_balance and 'bnb' in blockchain_balance:
            try:
                bnb_balance = float(blockchain_balance['bnb'])
            except (ValueError, TypeError):
                # If conversion fails, default to zero
                bnb_balance = 0.0
        
        # Format the database USDT balance to 2 decimal places for consistency
        formatted_database_balance = round(database_balance, 2)
                
        # Return database balance in balance.usdt field to maintain frontend compatibility
        return jsonify({
            'success': True,
            'balance': {
                'usdt': formatted_database_balance,  # Use database balance instead of blockchain balance
                'bnb': bnb_balance  # Use actual BNB balance from blockchain, not hardcoded
            },
            'blockchain_balance': blockchain_balance,  # Keep blockchain balance for reference
            'wallet_address': wallet_doc.get('deposit_address', ''),
            'qr_code_url': tatum_service.get_qr_code_url(wallet_doc.get('deposit_address', ''))
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@wallet_bp.route('/list', methods=['GET'])
@jwt_required()
def list_wallets():
    """List all wallets for the current user"""
    try:
        # Get user ID from JWT token
        current_user_id = get_user_id_from_jwt()
        
        # Try to convert to ObjectId if it's a string
        if isinstance(current_user_id, str):
            try:
                from bson.objectid import ObjectId
                current_user_id = ObjectId(current_user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
        
        # Get wallets from MongoDB
        wallet_docs = list(db.user_wallets.find({"user_id": current_user_id}))
        
        return jsonify({
            'success': True,
            'wallets': [
                {
                    'id': str(wallet_doc.get('_id')),
                    'address': wallet_doc.get('deposit_address', ''),
                    'blockchain': wallet_doc.get('blockchain', 'BSC'),
                    'created_at': wallet_doc.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if wallet_doc.get('created_at') else '',
                    'qr_code_url': tatum_service.get_qr_code_url(wallet_doc.get('deposit_address', '')),
                    'is_encrypted': wallet_doc.get('encrypted_private_key') is not None,
                    'encryption_version': wallet_doc.get('encryption_version')
                } for wallet_doc in wallet_docs
            ]
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@wallet_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get transaction history for the current user's wallet - fetched directly from Tatum.io API"""
    try:
        from datetime import datetime
        
        # Get user ID from JWT token
        current_user_id = get_user_id_from_jwt()
        
        # Try to convert to ObjectId if it's a string
        if isinstance(current_user_id, str):
            try:
                from bson.objectid import ObjectId
                current_user_id = ObjectId(current_user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
        
        # Get limit parameter from query string, default to 10
        limit = request.args.get('limit', 10, type=int)
        
        print(f"[TATUM_TX] Looking up transactions for user ID: {current_user_id}")
        
        # Find all wallet addresses associated with the current user
        wallet_docs = list(db.user_wallets.find({"user_id": current_user_id}))
        print(f"[TATUM_TX] Found {len(wallet_docs)} wallet documents")
        
        # Extract all wallet addresses
        wallet_addresses = []
        for wallet_doc in wallet_docs:
            address = wallet_doc.get('deposit_address', '')
            if address:
                wallet_addresses.append(address)
                print(f"[TATUM_TX] Found wallet address: {address}")
        
        print(f"[TATUM_TX] Total wallet addresses: {len(wallet_addresses)}")
        
        # Initialize the formatted transactions list
        formatted_transactions = []
        
        # Flag to track if we got any transactions from Tatum API
        tatum_transactions_found = False
        
        # First try to fetch transactions directly from Tatum.io API for each wallet address
        for wallet_address in wallet_addresses:
            if not wallet_address:
                continue
                
            print(f"[TATUM_TX] Querying Tatum API for transactions on address: {wallet_address}")
            
            try:
                # Define the chain we're using
                chain = 'bsc'  # Binance Smart Chain
                
                # Call Tatum API to get transactions for this address
                api_response = tatum_service.get_address_transactions(
                    chain=chain,
                    address=wallet_address,
                    pageSize=limit
                )
                
                print(f"[TATUM_TX] Tatum API response received: {api_response}")
                
                # Check if we got a valid response with transactions
                if api_response and isinstance(api_response, dict):
                    transactions = api_response.get('data', [])
                    
                    if transactions and len(transactions) > 0:
                        tatum_transactions_found = True
                        
                        for tx in transactions:
                            # Check if this is an incoming transaction (deposit)
                            is_deposit = tx.get('transactionSubtype') == 'incoming' or 'incoming' in tx.get('transactionSubtype', '')
                            
                            # Process both incoming transactions and token transfers 
                            if is_deposit or tx.get('transactionType') == 'fungible':
                                try:
                                    # Convert timestamp from milliseconds to datetime
                                    tx_timestamp = datetime.fromtimestamp(int(tx.get('timestamp', 0)) / 1000)
                                    formatted_time = tx_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                    
                                    # Determine currency and amount
                                    currency = 'BNB'  # Default for native transactions
                                    amount = float(tx.get('amount', 0))  # Amount is already in human-readable format
                                    
                                    # Check for token transfers (e.g., USDT)
                                    if tx.get('transactionType') == 'fungible' and tx.get('tokenAddress'):
                                        # USDT token address on BSC
                                        if tx.get('tokenAddress').lower() == '0x55d398326f99059ff775485246999027b3197955'.lower():
                                            currency = 'USDT'
                                        elif tx.get('tokenAddress'):
                                            # Use a generic token name for other tokens
                                            currency = 'TOKEN'
                                    
                                    # Create formatted transaction
                                    formatted_tx = {
                                        'txid': tx.get('hash', 'unknown'),
                                        'amount': float(tx.get('amount',0)),
                                        'currency': currency,
                                        'status': 'Completed',  # Transactions on blockchain are completed
                                        'network': 'BSC',       # Binance Smart Chain
                                        'timestamp': formatted_time,
                                        'type': 'Withdrwal' if float(tx.get('amount', 0))< 0 else'Deposit'
                                    }
                                    
                                    print(f"[TATUM_TX] Formatted Tatum transaction: {formatted_tx}")
                                    formatted_transactions.append(formatted_tx)
                                    
                                    # Check if this transaction exists in our database
                                    existing_tx = db.tatum_transactions.find_one({
                                        "$or": [
                                            {"tx_hash": tx.get('hash')},
                                            {"blockchain_tx_id": tx.get('hash')}
                                        ]
                                    })
                                    
                                    # If this is a new transaction, insert it and emit socket events
                                    if not existing_tx and currency == 'USDT':
                                        # Generate a unique transaction ID
                                        transaction_id = f"TX-{uuid.uuid4().hex[:8]}"
                                        now = datetime.utcnow()
                                        
                                        # Create transaction document
                                        tx_doc = {
                                            "transaction_id": transaction_id,
                                            "user_id": current_user_id,
                                            "tx_hash": tx.get('hash'),
                                            "amount": amount,
                                            "wallet_address": wallet_address.lower(),
                                            "status": "completed",
                                            "transaction_type": "deposit",
                                            "currency": currency,
                                            "created_at": now,
                                            "updated_at": now
                                        }
                                        
                                        # Insert into database
                                        print(f"[TATUM_TX] Inserting new transaction into database: {tx_doc}")
                                        db.tatum_transactions.insert_one(tx_doc)
                                        
                                        # Emit socket event for this transaction
                                        socketio.emit('new_deposit', {
                                            "transaction_id": transaction_id,
                                            "user_id": str(current_user_id),
                                            "amount": amount,
                                            "tx_hash": tx.get('hash'),
                                            "wallet_address": wallet_address,
                                            "currency": currency,
                                            "timestamp": now.isoformat(),
                                            "status": "Completed"
                                        }, broadcast=True)
                                        
                                        # Update user balance for USDT deposits
                                        if currency == 'USDT':
                                            user_doc = db.users.find_one({"_id": current_user_id})
                                            if user_doc:
                                                current_balance = float(user_doc.get('balance', 0))
                                                new_balance = current_balance + amount
                                                
                                                # Update balance in database
                                                db.users.update_one(
                                                    {"_id": current_user_id},
                                                    {"$set": {"balance": new_balance, "updated_at": now}}
                                                )
                                                
                                                # Emit balance update event
                                                socketio.emit('balance_updated', {
                                                    "user_id": str(current_user_id),
                                                    "balance": new_balance,
                                                    "transaction_id": transaction_id,
                                                    "timestamp": now.isoformat()
                                                }, room=str(current_user_id))
                                except Exception as e:
                                    print(f"[TATUM_TX] Error formatting Tatum transaction: {str(e)}")
                                    continue
                
            except Exception as e:
                print(f"[TATUM_TX] Error fetching from Tatum API for address {wallet_address}: {str(e)}")
        
        # If Tatum API shows no transactions, try direct Web3 lookup for recent blockchain transactions
        # This is useful for transactions that show on BSCScan but not yet in Tatum API
        if not formatted_transactions:
            print(f"[TATUM_TX] No transactions from Tatum API, trying direct Web3 lookup for BSCscan transactions")
            for wallet_address in wallet_addresses:
                if not wallet_address:
                    continue
                
                try:
                    # Use Web3 direct lookup through TatumHybridService
                    web3_response = tatum_service.get_web3_transactions(
                        chain='bsc',
                        address=wallet_address,
                        limit=limit
                    )
                    
                    web3_transactions = []
                    if isinstance(web3_response, dict):
                        web3_transactions = web3_response.get('data', [])
                    
                    if web3_transactions:
                        for tx in web3_transactions:
                            try:
                                tx_hash = tx.get('hash', '')
                                timestamp = int(tx.get('timeStamp', 0))
                                
                                # Convert timestamp to datetime
                                if timestamp:
                                    tx_time = datetime.fromtimestamp(timestamp)
                                    formatted_time = tx_time.strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    formatted_time = "Unknown"
                                
                                # Format the transaction for the frontend
                                formatted_tx = {
                                    'txid': tx_hash,
                                    'amount': float(tx.get('value', 0)) / 1e18,  # Convert from wei to ETH/BNB
                                    'currency': 'BNB',  # Default currency for direct blockchain transactions
                                    'status': 'Completed',
                                    'network': 'BSC',
                                    'timestamp': formatted_time,
                                    'type': 'Deposit'
                                }
                                
                                print(f"[TATUM_TX] Web3 transaction found: {formatted_tx}")
                                formatted_transactions.append(formatted_tx)
                                
                                # Check if this transaction exists in our database
                                existing_tx = db.tatum_transactions.find_one({
                                    "$or": [
                                        {"tx_hash": tx_hash},
                                        {"blockchain_tx_id": tx_hash}
                                    ]
                                })
                                
                                # If it's USDT and a new transaction, insert it and emit socket events
                                token_address = tx.get('tokenAddress', '').lower()
                                is_usdt = token_address == '0x55d398326f99059ff775485246999027b3197955'.lower()
                                
                                if not existing_tx and is_usdt:
                                    # Generate a unique transaction ID
                                    transaction_id = f"TX-{uuid.uuid4().hex[:8]}"
                                    now = datetime.utcnow()
                                    
                                    # Amount for USDT tokens should be properly scaled
                                    token_amount = float(tx.get('tokenValue', 0)) if 'tokenValue' in tx else float(tx.get('value', 0)) / 1e18
                                    
                                    # Create transaction document
                                    tx_doc = {
                                        "transaction_id": transaction_id,
                                        "user_id": current_user_id,
                                        "tx_hash": tx_hash,
                                        "amount": token_amount,
                                        "wallet_address": wallet_address.lower(),
                                        "status": "completed",
                                        "transaction_type": "deposit",
                                        "currency": 'USDT',
                                        "created_at": now,
                                        "updated_at": now
                                    }
                                    
                                    # Insert into database
                                    print(f"[TATUM_TX] Inserting new Web3 transaction into database: {tx_doc}")
                                    db.tatum_transactions.insert_one(tx_doc)
                                    
                                    # Emit socket event for this transaction
                                    socketio.emit('new_deposit', {
                                        "transaction_id": transaction_id,
                                        "user_id": str(current_user_id),
                                        "amount": token_amount,
                                        "tx_hash": tx_hash,
                                        "wallet_address": wallet_address,
                                        "currency": 'USDT',
                                        "timestamp": now.isoformat(),
                                        "status": "Completed"
                                    }, broadcast=True)
                                    
                                    # Update user balance
                                    user_doc = db.users.find_one({"_id": current_user_id})
                                    if user_doc:
                                        current_balance = float(user_doc.get('balance', 0))
                                        new_balance = current_balance + token_amount
                                        
                                        # Update balance in database
                                        db.users.update_one(
                                            {"_id": current_user_id},
                                            {"$set": {"balance": new_balance, "updated_at": now}}
                                        )
                                        
                                        # Emit balance update event
                                        socketio.emit('balance_updated', {
                                            "user_id": str(current_user_id),
                                            "balance": new_balance,
                                            "transaction_id": transaction_id,
                                            "timestamp": now.isoformat()
                                        }, room=str(current_user_id))
                            except Exception as e:
                                print(f"[TATUM_TX] Error formatting Web3 transaction: {str(e)}")
                                continue
                except Exception as e:
                    print(f"[TATUM_TX] Error in Web3 direct lookup: {str(e)}")
        
        # Even if we don't insert new transactions, always emit transactions_refreshed
        # This ensures the frontend gets the latest data
        socketio.emit('transactions_refreshed', {
            "transactions": formatted_transactions,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(current_user_id)
        })
        
        # Return only the transactions array as that's what the frontend expects
        return jsonify({
            'transactions': formatted_transactions
        }), 200
    
    except Exception as e:
        print(f"[TATUM_TX] Error in get_transactions: {str(e)}")
        import traceback
        print(f"[TATUM_TX] Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@wallet_bp.route('/security-info', methods=['GET'])
@jwt_required()
def wallet_security_info():
    """Get security information about the user's wallets"""
    try:
        # Get user ID from JWT token
        current_user_id = get_user_id_from_jwt()
        
        # Try to convert to ObjectId if it's a string
        if isinstance(current_user_id, str):
            try:
                from bson.objectid import ObjectId
                current_user_id = ObjectId(current_user_id)
            except:
                # Keep as string if not a valid ObjectId
                pass
        
        # Get wallets from MongoDB
        wallet_docs = list(db.user_wallets.find({"user_id": current_user_id}))
        
        # Calculate security stats
        total_wallets = len(wallet_docs)
        encrypted_wallets = sum(1 for wallet_doc in wallet_docs if wallet_doc.get('encrypted_private_key') is not None)
        encryption_versions = {}
        
        for wallet_doc in wallet_docs:
            encryption_version = wallet_doc.get('encryption_version')
            if encryption_version:
                encryption_versions[encryption_version] = encryption_versions.get(encryption_version, 0) + 1
        
        # Get latest encryption rotation info from MongoDB (if applicable)
        from datetime import datetime
        latest_rotation_doc = db.encryption_key_rotations.find_one({}, sort=[("created_at", -1)])
        
        # Log security check activity to MongoDB
        activity_doc = {
            "user_id": current_user_id,
            "activity_type": 'security_check',
            "activity_description": 'User verified wallet security status',
            "created_at": datetime.utcnow()
        }
        db.user_activities.insert_one(activity_doc)
        
        return jsonify({
            'success': True,
            'security_status': {
                'total_wallets': total_wallets,
                'encrypted_wallets': encrypted_wallets,
                'security_percentage': (encrypted_wallets / total_wallets * 100) if total_wallets > 0 else 0,
                'encryption_versions': encryption_versions,
                'latest_security_update': latest_rotation_doc.get('created_at').strftime('%Y-%m-%d') if latest_rotation_doc and latest_rotation_doc.get('created_at') else None,
                'user_wallets': [
                    {
                        'address': wallet_doc.get('deposit_address', ''),
                        'is_encrypted': wallet_doc.get('encrypted_private_key') is not None,
                        'encryption_version': wallet_doc.get('encryption_version'),
                        'encryption_date': wallet_doc.get('key_encrypted_at').strftime('%Y-%m-%d %H:%M:%S') if wallet_doc.get('key_encrypted_at') else None
                    } for wallet_doc in wallet_docs
                ]
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500