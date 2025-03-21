"""
Socket.IO event handlers for real-time updates

This module implements Socket.IO event handlers for real-time updates,
particularly focused on transaction processing.
"""

from flask_socketio import emit, join_room, leave_room
from flask import current_app, request
from app import socketio, db
from flask_jwt_extended import decode_token
import jwt
import uuid
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to store users with paused socket operations
socket_paused_users = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection with JWT authentication"""
    from flask_socketio import ConnectionRefusedError
    try:
        # Get token from different possible sources
        token = None
        
        # Check authorization header
        auth_header = request.headers.get('Authorization', '') if hasattr(request, 'headers') else ''
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
        
        # Check query parameters
        if not token and hasattr(request, 'args'):
            token = request.args.get('token')
        
        # Check Socket.IO auth data
        if not token and hasattr(request, 'event') and request.event.get('args'):
            auth_data = request.event.get('args', {}).get('auth', {})
            token = auth_data.get('token')
            
        # If we found a token, validate it
        if token:
            try:
                # Decode token - adjust this to match your JWT structure
                decode_token(token)
                logger.info("Client authenticated with valid JWT token")
            except jwt.ExpiredSignatureError:
                logger.warning("Expired JWT token in socket connection")
                # Optionally reject connection for expired token
                # return ConnectionRefusedError('Authentication expired')
            except Exception as jwt_error:
                logger.warning(f"Invalid JWT token in socket connection: {str(jwt_error)}")
                # Optionally reject connection for invalid token
                # return ConnectionRefusedError('Invalid authentication')
        else:
            logger.warning("No auth token provided for socket connection")
            # Uncomment to reject connection if no token:
            # return ConnectionRefusedError('Authentication required')
            
        # Get the Socket.IO session ID from Flask request context
        session_id = request.sid if hasattr(request, 'sid') else 'unknown'
        logger.info(f"Client connected: {session_id}")
        emit('connection_status', {"status": "connected", "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error(f"Error in handle_connect: {str(e)}")
        return ConnectionRefusedError('Connection error')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    # Use a safer method to log disconnection
    logger.info("Client disconnected")

@socketio.on('pause_socket_operations')
def pause_socket_operations(data):
    """
    Temporarily pause socket processing for a specific user
    during Tatum API operations
    
    Args:
        data: Dictionary containing user_id and optional duration
    """
    try:
        user_id = data.get('user_id')
        if not user_id:
            emit('pause_error', {"error": "User ID required"})
            return
            
        duration = data.get('duration', 30)  # Default 30 seconds
        
        # Set pause until timestamp
        pause_until = datetime.utcnow() + timedelta(seconds=duration)
        socket_paused_users[user_id] = pause_until
        
        logger.info(f"Socket operations paused for user {user_id} until {pause_until.isoformat()}")
        
        emit('socket_operations_paused', {
            "user_id": user_id,
            "paused_until": pause_until.isoformat()
        })
    except Exception as e:
        logger.error(f"Error pausing socket operations: {str(e)}")
        emit('pause_error', {"error": str(e)})

@socketio.on('resume_socket_operations')
def resume_socket_operations(data):
    """
    Resume socket operations for a user
    
    Args:
        data: Dictionary containing user_id
    """
    try:
        user_id = data.get('user_id')
        if not user_id:
            emit('resume_error', {"error": "User ID required"})
            return
            
        # Remove user from paused list
        if user_id in socket_paused_users:
            del socket_paused_users[user_id]
            
        logger.info(f"Socket operations resumed for user {user_id}")
        
        emit('socket_operations_resumed', {"user_id": user_id})
    except Exception as e:
        logger.error(f"Error resuming socket operations: {str(e)}")
        emit('resume_error', {"error": str(e)})

def is_socket_paused_for_user(user_id):
    """
    Check if socket operations are paused for a user
    
    Args:
        user_id: User ID to check
        
    Returns:
        bool: True if operations are paused, False otherwise
    """
    if user_id in socket_paused_users:
        pause_until = socket_paused_users[user_id]
        now = datetime.utcnow()
        
        # If pause period has expired, remove from paused list
        if now > pause_until:
            del socket_paused_users[user_id]
            return False
            
        return True
        
    return False

@socketio.on('save_deposit')
def handle_deposit(deposit_data):
    """
    Handle deposit transaction data and update user balance
    
    Args:
        deposit_data: Deposit transaction data with user_id and amount
    """
    try:
        logger.info(f"Received deposit data: {deposit_data}")
        
        # Validate required fields for deposit
        required_fields = ['user_id', 'amount', 'wallet_address', 'tx_hash']
        for field in required_fields:
            if field not in deposit_data:
                emit('deposit_error', {"error": f"Missing required field: {field}"})
                return
        
        # Check if operations are paused for this user
        user_id = deposit_data.get('user_id')
        if is_socket_paused_for_user(user_id):
            logger.info(f"Socket operations paused for user {user_id}, queuing deposit")
            emit('deposit_queued', {
                "status": "queued",
                "message": "Your deposit will be processed shortly"
            })
            return
        
        # Normalize wallet address (convert to lowercase)
        if 'wallet_address' in deposit_data and deposit_data['wallet_address']:
            deposit_data['wallet_address'] = deposit_data['wallet_address'].lower()
            logger.info(f"Normalized wallet address: {deposit_data['wallet_address']}")
        
        # Add transaction metadata
        deposit_data['transaction_type'] = 'deposit'
        deposit_data['timestamp'] = datetime.utcnow()
        deposit_data['transaction_id'] = f"DEP-{uuid.uuid4().hex[:8]}"
        deposit_data['status'] = 'completed'
        
        # Store in MongoDB tatum_transactions collection
        result = db.tatum_transactions.insert_one(deposit_data)
        transaction_id = str(result.inserted_id)
        
        logger.info(f"Deposit transaction saved with ID: {transaction_id}")
        
        # Update user balance in database
        user_id = deposit_data['user_id']
        amount = deposit_data['amount']
        
        # Get current user balance
        user = db.users.find_one({"_id": user_id})
        current_balance = user.get('balance', 0) if user else 0
        new_balance = current_balance + amount
        
        # Update the user's balance
        now = datetime.utcnow()
        db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "balance": new_balance,
                "updated_at": now
            }}
        )
        
        logger.info(f"Updated user {user_id} balance from {current_balance} to {new_balance}")
        
        # Emit confirmation to the client
        emit('deposit_saved', {
            "id": transaction_id,
            "transaction_id": deposit_data['transaction_id'],
            "user_id": user_id,
            "amount": amount,
            "new_balance": new_balance,
            "timestamp": deposit_data['timestamp'].isoformat()
        })
        
        # Broadcast deposit event to all connected clients
        broadcast_data = {
            "transaction_id": deposit_data['transaction_id'],
            "transaction_type": 'deposit',
            "amount": amount,
            "wallet_address": deposit_data['wallet_address'],
            "timestamp": deposit_data['timestamp'].isoformat()
        }
        
        emit('new_deposit', broadcast_data, broadcast=True)
        
        # Also broadcast updated balance for the specific user
        emit('balance_updated', {
            "user_id": user_id,
            "balance": new_balance,
            "transaction_id": deposit_data['transaction_id'],
            "timestamp": deposit_data['timestamp'].isoformat()
        }, room=user_id)
    
    except Exception as e:
        logger.error(f"Error handling deposit: {str(e)}")
        emit('deposit_error', {"error": str(e)})

@socketio.on('save_transaction')
def handle_transaction(tx_data):
    """
    Handle transaction data sent from client and save to MongoDB
    
    Args:
        tx_data: Transaction data object containing transaction details
    """
    try:
        logger.info(f"Received transaction data: {tx_data}")
        
        # Validate required fields
        required_fields = ['user_id', 'transaction_type', 'amount']
        for field in required_fields:
            if field not in tx_data:
                emit('transaction_error', {"error": f"Missing required field: {field}"})
                return
        
        # Check if operations are paused for this user
        user_id = tx_data.get('user_id')
        if is_socket_paused_for_user(user_id):
            logger.info(f"Socket operations paused for user {user_id}, queuing transaction")
            emit('transaction_queued', {
                "status": "queued",
                "message": "Your transaction will be processed shortly"
            })
            return
        
        # Normalize addresses in transaction data
        if 'wallet_address' in tx_data and tx_data['wallet_address']:
            tx_data['wallet_address'] = tx_data['wallet_address'].lower()
        if 'to_address' in tx_data and tx_data['to_address']:
            tx_data['to_address'] = tx_data['to_address'].lower()
        if 'from_address' in tx_data and tx_data['from_address']:
            tx_data['from_address'] = tx_data['from_address'].lower()
            
        logger.info(f"Normalized transaction addresses")
        
        # If this is a deposit transaction, use the specialized handler
        if tx_data.get('transaction_type') == 'deposit':
            # We're missing some required fields for deposits, so add defaults
            if 'wallet_address' not in tx_data and 'to_address' in tx_data:
                tx_data['wallet_address'] = tx_data['to_address']
            if 'tx_hash' not in tx_data and 'blockchain_tx_id' in tx_data:
                tx_data['tx_hash'] = tx_data['blockchain_tx_id']
            
            # Ensure required fields are present with defaults if needed
            if 'wallet_address' not in tx_data:
                tx_data['wallet_address'] = 'unknown'
            if 'tx_hash' not in tx_data:
                tx_data['tx_hash'] = f"MANUAL-{uuid.uuid4().hex[:8]}"
                
            return handle_deposit(tx_data)
        
        # Add timestamp and ID if not provided
        if 'timestamp' not in tx_data:
            tx_data['timestamp'] = datetime.utcnow()
        
        if 'transaction_id' not in tx_data:
            tx_data['transaction_id'] = f"SOCKET-{uuid.uuid4().hex[:8]}"
        
        # Store in MongoDB tatum_transactions collection
        result = db.tatum_transactions.insert_one(tx_data)
        transaction_id = str(result.inserted_id)
        
        logger.info(f"Transaction saved with ID: {transaction_id}")
        
        # Emit confirmation to the client
        emit('transaction_saved', {
            "id": transaction_id,
            "transaction_id": tx_data.get('transaction_id'),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Broadcast to all connected clients if this is meant to be a public transaction
        if tx_data.get('broadcast', False):
            # Remove sensitive info before broadcasting
            broadcast_data = {
                "transaction_id": tx_data.get('transaction_id'),
                "transaction_type": tx_data.get('transaction_type'),
                "amount": tx_data.get('amount'),
                "timestamp": datetime.utcnow().isoformat()
            }
            # Add transaction-specific fields based on type
            if tx_data.get('transaction_type') == 'withdrawal':
                broadcast_data['withdrawal_address'] = tx_data.get('from_address')
                
            emit('new_transaction', broadcast_data, broadcast=True)
    
    except Exception as e:
        logger.error(f"Error handling transaction: {str(e)}")
        emit('transaction_error', {"error": str(e)})

@socketio.on('join')
def handle_join(data):
    """
    Handle joining a room for user-specific updates
    
    Args:
        data: Dictionary containing room information
    """
    try:
        room = data.get('room')
        if not room:
            emit('join_error', {"error": "Room parameter is required"})
            return
            
        # Join the specified room (user ID)
        join_room(room)
        logger.info(f"Client {request.sid} joined room: {room}")
        emit('joined_room', {"room": room, "status": "joined"})
    except Exception as e:
        logger.error(f"Error joining room: {str(e)}")
        emit('join_error', {"error": str(e)})

@socketio.on('external_transaction')
def handle_external_transaction(tx_data):
    """
    Handle transactions detected from external blockchain explorers (BSCscan, etc.).
    This ensures transactions showing in blockchain explorers appear in the dashboard.
    
    Args:
        tx_data: Transaction data from external blockchain source
        Required fields:
        - tx_hash: Transaction hash from the blockchain
        - wallet_address: Wallet address (recipient)
        - amount: Transaction amount
        - token: Token type (e.g., 'BNB', 'USDT')
    """
    logger.info(f"Processing external blockchain transaction: {tx_data}")
    
    try:
        # Check if operations are paused for this user
        user_id = tx_data.get('user_id')
        if user_id and is_socket_paused_for_user(user_id):
            logger.info(f"Socket operations paused for user {user_id}, queuing external transaction")
            emit('transaction_queued', {
                "status": "queued",
                "message": "Your transaction will be processed shortly"
            })
            return
            
        # Normalize the wallet address (convert to lowercase) for consistent matching
        wallet_address = tx_data.get('wallet_address', '').lower()
        if not wallet_address:
            emit('transaction_error', {'error': 'Missing wallet address'})
            return
        
        # Find the user associated with this wallet address
        user = db.users.find_one({"wallet_address": {'$regex': wallet_address, '$options': 'i'}})
        
        if not user:
            logger.error(f"No user found with wallet address: {wallet_address}")
            # Search for partial address matches as a fallback
            users_with_similar_address = list(db.users.find(
                {"wallet_address": {"$regex": wallet_address[:20], "$options": "i"}}
            ))
            
            if users_with_similar_address:
                logger.info(f"Found {len(users_with_similar_address)} users with similar wallet address")
                user = users_with_similar_address[0]  # Use the first match
            else:
                emit('transaction_error', {'error': 'User not found for wallet address'})
                return
        
        # Now check if operations are paused for the found user
        user_id = user['_id']
        if is_socket_paused_for_user(user_id):
            logger.info(f"Socket operations paused for user {user_id}, queuing external transaction")
            emit('transaction_queued', {
                "status": "queued", 
                "message": "Your transaction will be processed shortly"
            })
            return
            
        # Generate a unique transaction ID
        tx_id = f"EXT-{uuid.uuid4().hex[:8]}"
        
        # Create transaction record
        transaction = {
            "transaction_id": tx_id,
            "user_id": user['_id'],
            "transaction_type": "deposit",
            "amount": float(tx_data.get('amount', 0)),
            "blockchain_tx_id": tx_data.get('tx_hash'),
            "wallet_address": wallet_address,
            "status": "completed",
            "token": tx_data.get('token', 'USDT'),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert transaction into database
        result = db.tatum_transactions.insert_one(transaction)
        transaction_id = result.inserted_id
        
        logger.info(f"Saved external transaction with ID: {transaction_id}")
        
        # Update user balance
        previous_balance = float(user.get('balance', 0))
        new_balance = previous_balance + float(tx_data.get('amount', 0))
        
        db.users.update_one(
            {"_id": user['_id']},
            {"$set": {"balance": new_balance, "updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"Updated user balance from {previous_balance} to {new_balance}")
        
        # Emit events to notify clients
        # 1. Transaction saved confirmation
        emit('transaction_saved', {
            "id": str(transaction_id),
            "transaction_id": tx_id
        })
        
        # 2. New deposit for all clients
        emit('new_deposit', {
            "transaction_id": tx_id,
            "user_id": str(user['_id']),
            "amount": tx_data.get('amount', 0),
            "tx_hash": tx_data.get('tx_hash'),
            "wallet_address": wallet_address,
            "timestamp": datetime.utcnow().isoformat()
        }, broadcast=True)
        
        # 3. Balance update for specific user
        user_room = str(user['_id'])
        emit('balance_updated', {
            "user_id": str(user['_id']),
            "balance": new_balance,
            "previous_balance": previous_balance,
            "change": float(tx_data.get('amount', 0)),
            "timestamp": datetime.utcnow().isoformat()
        }, room=user_room)
        
        return {
            "success": True,
            "id": str(transaction_id),
            "new_balance": new_balance
        }
    
    except Exception as e:
        logger.error(f"Error processing external transaction: {str(e)}")
        emit('transaction_error', {'error': str(e)})
        return {"success": False, "error": str(e)}

def init_socket_handlers():
    """
    Initialize socket handlers
    
    This function is called from the application factory to register socket handlers
    """
    # Import additional handler modules here if needed
    logger.info("Socket.IO handlers initialized")
    return True