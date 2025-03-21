# app/api/admin.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
import os
from datetime import datetime
from bson.objectid import ObjectId

admin_bp = Blueprint('admin', __name__)

# Helper function for admin privilege check
def admin_required(f):
    """Decorator to require admin role for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        # Check if user is admin
        from app import db
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin privileges required for this action'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# New endpoint to fetch users with their sponsor IDs
@admin_bp.route('/users-sponsor-ids', methods=['GET'])
@jwt_required()
@admin_required
def get_users_with_sponsor_ids():
    """
    Get all users with their properly formatted sponsor IDs
    Returns users sorted by sponsor_id by default
    """
    try:
        from app import db
        
        # Get query parameters
        sort_by = request.args.get('sort_by', 'sponsor_id')  # Default sort by sponsor_id
        sort_order = request.args.get('sort_order', 'asc')   # Default ascending order
        limit = request.args.get('limit', 100, type=int)     # Default limit 100 users
        page = request.args.get('page', 1, type=int)         # Default page 1
        
        # Build query with sorting
        sort_direction = 1 if sort_order.lower() == 'asc' else -1
        sort_field = sort_by if sort_by in ['sponsor_id', 'created_at'] else '_id'
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Query MongoDB with pagination
        users = list(db.users.find().sort(sort_field, sort_direction).skip(skip).limit(limit))
        
        # Get total count for pagination
        total_users = db.users.count_documents({})
        
        # Format user data with proper sponsor IDs
        formatted_users = []
        for user in users:
            # Ensure sponsor_id is properly formatted (AL0000001 format)
            sponsor_id = user.get('sponsor_id') if user.get('sponsor_id') else f"AL{str(user.get('_id')).zfill(7)}"
            
            # Get referrer information if available
            referrer = None
            referral_entry = db.referral_tree.find_one({"user_id": user.get('_id')})
            
            if referral_entry and referral_entry.get('referrer_id'):
                referrer_id = referral_entry.get('referrer_id')
                if isinstance(referrer_id, str) and ObjectId.is_valid(referrer_id):
                    referrer_id = ObjectId(referrer_id)
                
                referrer_user = db.users.find_one({"_id": referrer_id})
                if referrer_user:
                    referrer = {
                        'id': str(referrer_user.get('_id')),
                        'sponsor_id': referrer_user.get('sponsor_id') or f"AL{str(referrer_user.get('_id')).zfill(7)}",
                        'name': referrer_user.get('user_name')
                    }
            
            # Format basic user data
            user_data = {
                'id': str(user.get('_id')),
                'sponsor_id': sponsor_id,
                'name': user.get('user_name'),
                'email': user.get('email'),
                'created_at': user.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if user.get('created_at') else None,
                'referred_by': referrer,
                'balance': float(user.get('balance')) if user.get('balance') is not None else 0.0
            }
            
            formatted_users.append(user_data)
        
        # Calculate pagination info
        total_pages = (total_users + limit - 1) // limit  # Ceiling division
        
        # Return formatted response with pagination info
        return jsonify({
            'success': True,
            'users': formatted_users,
            'pagination': {
                'total_items': total_users,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': limit
            }
        }), 200
        
    except Exception as e:
        print(f"Error fetching users with sponsor IDs: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    """Get admin dashboard statistics - only accessible to admins"""
    try:
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        # Check if user is admin
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get system statistics
        total_users = db.users.count_documents({})
        active_users = db.users.count_documents({"is_active": True})
        total_investments = db.user_investments.count_documents({})
        
        # Aggregate sum of investment amounts
        investment_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        investment_result = list(db.user_investments.aggregate(investment_pipeline))
        total_investment_amount = investment_result[0]['total'] if investment_result else 0
        
        # Aggregate sum of earnings
        earnings_pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        earnings_result = list(db.user_earnings.aggregate(earnings_pipeline))
        total_earnings = earnings_result[0]['total'] if earnings_result else 0
        
        # Current cycle status
        current_cycle = db.bid_cycles.find_one({}, sort=[("_id", -1)])
        
        # Pending withdrawals
        pending_withdrawals = db.withdrawals.count_documents({"withdrawal_status": "pending"})
        
        # Aggregate sum of pending withdrawal amounts
        withdrawal_pipeline = [
            {"$match": {"withdrawal_status": "pending"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        withdrawal_result = list(db.withdrawals.aggregate(withdrawal_pipeline))
        pending_withdrawal_amount = withdrawal_result[0]['total'] if withdrawal_result else 0
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_users': total_users,
                'active_users': active_users,
                'total_investments': total_investments,
                'total_investment_amount': float(total_investment_amount),
                'total_earnings_distributed': float(total_earnings),
                'pending_withdrawals': pending_withdrawals,
                'pending_withdrawal_amount': float(pending_withdrawal_amount),
                'current_cycle': {
                    'id': str(current_cycle.get('_id')) if current_cycle else None,
                    'date': current_cycle.get('cycle_date').strftime('%Y-%m-%d') if current_cycle and current_cycle.get('cycle_date') else None,
                    'status': current_cycle.get('cycle_status') if current_cycle else None,
                    'filled': current_cycle.get('bids_filled') if current_cycle else 0,
                    'total': current_cycle.get('total_bids_allowed') if current_cycle else 0
                }
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users - admin only"""
    try:
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        # Check if user is admin
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get all users with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Calculate skip for pagination
        skip = (page - 1) * per_page
        
        # Get users with pagination
        users = list(db.users.find().skip(skip).limit(per_page))
        total = db.users.count_documents({})
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        # Convert user documents to dictionaries for JSON serialization
        user_dicts = []
        for user in users:
            user_dict = dict(user)
            # Convert ObjectId to string
            user_dict['_id'] = str(user_dict['_id'])
            # Convert datetime objects to strings
            for key, value in user_dict.items():
                if isinstance(value, datetime):
                    user_dict[key] = value.isoformat()
            user_dicts.append(user_dict)
        
        return jsonify({
            'success': True,
            'users': user_dicts,
            'total': total,
            'pages': total_pages,
            'current_page': page
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Transaction Management Endpoints

@admin_bp.route('/withdrawals', methods=['GET'])
@jwt_required()
def get_pending_withdrawals():
    """Get all pending withdrawal requests"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get all pending withdrawals
        pending = list(db.withdrawals.find({"withdrawal_status": "pending"}))
        
        withdrawals = []
        for w in pending:
            # Get user details
            w_user_id = w.get('user_id')
            if isinstance(w_user_id, str) and ObjectId.is_valid(w_user_id):
                w_user_id = ObjectId(w_user_id)
                
            user = db.users.find_one({"_id": w_user_id})
            username = user.get('user_name') if user else "Unknown"
            
            withdrawals.append({
                'id': str(w.get('_id')),
                'user_id': str(w.get('user_id')),
                'username': username,
                'amount': float(w.get('amount')),
                'wallet_address': w.get('wallet_address'),
                'created_at': w.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if w.get('created_at') else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'withdrawals': withdrawals,
            'count': len(withdrawals)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/withdrawals/process/<withdrawal_id>', methods=['POST'])
@jwt_required()
def process_withdrawal(withdrawal_id):
    """Process a pending withdrawal"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Initialize transaction service
        from app.services.transaction_service import TransactionService
        transaction_service = TransactionService()
        
        # Get withdrawal
        if ObjectId.is_valid(withdrawal_id):
            withdrawal_id = ObjectId(withdrawal_id)
            
        withdrawal = db.withdrawals.find_one({"_id": withdrawal_id})
        
        if not withdrawal:
            return jsonify({'success': False, 'message': 'Withdrawal not found'}), 404
            
        if withdrawal.get('withdrawal_status') != 'pending':
            return jsonify({'success': False, 'message': f'Withdrawal is already {withdrawal.get("withdrawal_status")}'}, 400)
            
        # Process the withdrawal using secure key handling
        result = transaction_service.send_usdt(
            from_user_id=withdrawal.get('user_id'),
            to_address=withdrawal.get('wallet_address'),
            amount=float(withdrawal.get('amount')),
            admin_id=current_user_id  # Use admin_id instead of plaintext key
        )
        
        if not result['success']:
            return jsonify(result), 500
            
        # Update withdrawal status
        db.withdrawals.update_one(
            {"_id": withdrawal_id},
            {
                "$set": {
                    "withdrawal_status": "processed",
                    "transaction_hash": result.get('tx_hash', ''),
                    "processed_at": datetime.utcnow()
                }
            }
        )
        
        return jsonify({
            'success': True,
            'withdrawal_id': str(withdrawal_id),
            'tx_hash': result.get('tx_hash', ''),
            'message': 'Withdrawal processed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/withdrawals/reject/<withdrawal_id>', methods=['POST'])
@jwt_required()
def reject_withdrawal(withdrawal_id):
    """Reject a pending withdrawal"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get reason from request
        data = request.json
        reason = data.get('reason', 'Rejected by admin')
        
        # Get withdrawal
        if ObjectId.is_valid(withdrawal_id):
            withdrawal_id = ObjectId(withdrawal_id)
            
        withdrawal = db.withdrawals.find_one({"_id": withdrawal_id})
        
        if not withdrawal:
            return jsonify({'success': False, 'message': 'Withdrawal not found'}), 404
            
        if withdrawal.get('withdrawal_status') != 'pending':
            return jsonify({'success': False, 'message': f'Withdrawal is already {withdrawal.get("withdrawal_status")}'}, 400)
        
        # Get user
        user_id = withdrawal.get('user_id')
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_id = ObjectId(user_id)
            
        # Update user's balance
        db.users.update_one(
            {"_id": user_id},
            {"$inc": {"balance": withdrawal.get('amount')}}
        )
        
        # Update withdrawal status
        db.withdrawals.update_one(
            {"_id": withdrawal_id},
            {
                "$set": {
                    "withdrawal_status": "rejected",
                    "processed_at": datetime.utcnow()
                }
            }
        )
        
        # Add activity log
        activity = {
            "user_id": user_id,
            "activity_type": "withdrawal_rejected",
            "activity_description": f"Withdrawal of {withdrawal.get('amount')} USDT rejected: {reason}",
            "created_at": datetime.utcnow()
        }
        
        db.user_activities.insert_one(activity)
        
        return jsonify({
            'success': True,
            'withdrawal_id': str(withdrawal_id),
            'message': 'Withdrawal rejected and amount refunded'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/daily-returns/distribute', methods=['POST'])
@jwt_required()
def distribute_daily_returns():
    """Distribute daily returns for all active investments"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Initialize transaction service
        from app.services.transaction_service import TransactionService
        transaction_service = TransactionService()
        
        # Run distribution process
        result = transaction_service.distribute_daily_returns()
        
        if not result['success']:
            return jsonify(result), 500
            
        return jsonify({
            'success': True,
            'processed': result.get('processed', 0),
            'completed': result.get('completed', 0),
            'failed': result.get('failed', 0),
            'message': 'Daily returns distributed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/team-rewards/calculate', methods=['POST'])
@jwt_required()
def calculate_team_rewards():
    """Calculate and distribute team rewards"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Initialize transaction service
        from app.services.transaction_service import TransactionService
        transaction_service = TransactionService()
        
        # Get all users with sufficient active legs
        from app.services.system_service import get_system_setting
        
        min_legs = int(get_system_setting('min_legs_for_reward', 5))
        eligible_legs = list(db.user_legs.find({"active_legs": {"$gte": min_legs}}))
        
        if not eligible_legs:
            return jsonify({
                'success': True,
                'message': 'No users with sufficient active legs found',
                'count': 0
            }), 200
        
        # Get team reward levels from database
        reward_levels = list(db.team_rewards.find({"is_active": 1}).sort("business_volume", 1))
        
        if not reward_levels:
            return jsonify({
                'success': False, 
                'message': 'No active reward levels defined'
            }), 400
        
        # Process each eligible user
        processed_count = 0
        failed_count = 0
        total_amount = 0
        
        for legs in eligible_legs:
            try:
                user_id = legs.get('user_id')
                if isinstance(user_id, str) and ObjectId.is_valid(user_id):
                    user_id = ObjectId(user_id)
                
                # Get user's business volume
                business = db.team_business.find_one({"user_id": user_id})
                
                if not business:
                    continue
                
                # Find matching reward level
                reward_level = None
                for level in sorted(reward_levels, key=lambda x: x.get('business_volume', 0), reverse=True):
                    if business.get('business_volume', 0) >= level.get('business_volume', 0):
                        reward_level = level
                        break
                
                if not reward_level:
                    continue
                
                # Check if current rank is different from calculated rank
                if business.get('current_rank_level') != reward_level.get('rank_level'):
                    # User has reached a new rank, distribute reward
                    result = transaction_service.process_team_reward(
                        user_id=user_id,
                        amount=float(reward_level.get('reward_amount')),
                        team_level=reward_level.get('rank_level')
                    )
                    
                    if result['success']:
                        # Update rank level
                        db.team_business.update_one(
                            {"_id": business.get('_id')},
                            {"$set": {"current_rank_level": reward_level.get('rank_level')}}
                        )
                        processed_count += 1
                        total_amount += float(reward_level.get('reward_amount'))
                    else:
                        failed_count += 1
                
                # Update last calculated timestamp
                db.team_business.update_one(
                    {"_id": business.get('_id')},
                    {"$set": {"last_calculated_at": datetime.utcnow()}}
                )
                
            except Exception as e:
                print(f"Error processing team reward for user {legs.get('user_id')}: {str(e)}")
                failed_count += 1
                continue
        
        return jsonify({
            'success': True,
            'processed': processed_count,
            'failed': failed_count,
            'total_amount': total_amount,
            'message': 'Team rewards calculated and distributed'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/system-settings', methods=['GET'])
@jwt_required()
def get_system_settings():
    """Get all system settings"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get all settings
        settings_list = list(db.system_settings.find())
        
        result = {}
        for setting in settings_list:
            result[setting.get('setting_key')] = setting.get('setting_value')
        
        return jsonify({
            'success': True,
            'settings': result
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/system-settings/update', methods=['POST'])
@jwt_required()
def update_system_settings():
    """Update system settings"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get settings to update
        data = request.json
        
        if not data or not isinstance(data, dict):
            return jsonify({'success': False, 'message': 'Invalid data format'}), 400
        
        # Update each setting
        updated_settings = []
        for key, value in data.items():
            # Find and update setting
            db.system_settings.update_one(
                {"setting_key": key},
                {"$set": {"setting_value": str(value)}},
                upsert=False
            )
            updated_settings.append(key)
        
        # Log the activity
        log = {
            "log_type": "settings_update",
            "log_message": f"System settings updated: {', '.join(updated_settings)}",
            "created_at": datetime.utcnow()
        }
        
        db.system_logs.insert_one(log)
        
        return jsonify({
            'success': True,
            'updated': updated_settings,
            'message': 'System settings updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Wallet Security Management Endpoints

@admin_bp.route('/wallet/encryption-status', methods=['GET'])
@jwt_required()
def wallet_encryption_status():
    """Get encryption status of all wallets"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get wallet encryption statistics
        total_wallets = db.user_wallets.count_documents({})
        encrypted_wallets = db.user_wallets.count_documents({"encrypted_private_key": {"$ne": None}})
        unencrypted_wallets = total_wallets - encrypted_wallets
        
        # Get encryption version statistics
        v1_wallets = db.user_wallets.count_documents({"encryption_version": "v1"})
        v2_wallets = db.user_wallets.count_documents({"encryption_version": "v2"})
        
        # Get most recent key rotation
        latest_rotation = db.encryption_key_rotations.find_one(
            sort=[("created_at", -1)]
        )
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_wallets': total_wallets,
                'encrypted_wallets': encrypted_wallets,
                'unencrypted_wallets': unencrypted_wallets,
                'encryption_versions': {
                    'v1': v1_wallets,
                    'v2': v2_wallets
                },
                'latest_key_rotation': {
                    'date': latest_rotation.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if latest_rotation and latest_rotation.get('created_at') else None,
                    'status': latest_rotation.get('status') if latest_rotation else None
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/wallet/encrypt', methods=['POST'])
@jwt_required()
def encrypt_wallets():
    """Encrypt all unencrypted wallet private keys"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get request data
        data = request.json
        reason = data.get('reason', 'Initial wallet encryption')
        
        # Get unencrypted wallets
        unencrypted_wallets = list(db.user_wallets.find({
            "encrypted_private_key": None,
            "private_key": {"$ne": None}
        }))
        
        if not unencrypted_wallets:
            return jsonify({
                'success': True,
                'encrypted': 0,
                'message': 'No unencrypted wallets found with private keys'
            }), 200
        
        # Initialize encryption service
        from app.services.encryption_service import EncryptionService
        encryption_service = EncryptionService()
        
        # Encrypt each wallet
        encrypted_count = 0
        failed_count = 0
        
        for wallet in unencrypted_wallets:
            try:
                wallet_id = wallet.get('_id')
                user_id = wallet.get('user_id')
                
                if not wallet.get('private_key'):
                    continue
                
                # Ensure proper ObjectId handling
                if isinstance(user_id, str) and ObjectId.is_valid(user_id):
                    user_id = ObjectId(user_id)
                    
                # Encrypt the private key
                encrypted_key = encryption_service.encrypt_private_key(
                    wallet.get('private_key'),
                    user_id
                )
                
                if encrypted_key:
                    # Update wallet
                    db.user_wallets.update_one(
                        {"_id": wallet_id},
                        {
                            "$set": {
                                "encrypted_private_key": encrypted_key,
                                "encryption_version": "v1",
                                "key_encrypted_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    # Log access
                    log = {
                        "wallet_id": wallet_id,
                        "user_id": user_id,
                        "admin_id": current_user_id,
                        "access_type": "encryption",
                        "access_reason": reason,
                        "accessed_at": datetime.utcnow()
                    }
                    
                    db.wallet_key_access_logs.insert_one(log)
                    encrypted_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error encrypting wallet {wallet.get('_id')}: {str(e)}")
                failed_count += 1
                continue
        
        # Log the activity
        log = {
            "log_type": "wallet_encryption",
            "log_message": f"Admin {current_user_id} encrypted {encrypted_count} wallets. Reason: {reason}",
            "created_at": datetime.utcnow()
        }
        
        db.system_logs.insert_one(log)
        
        # Clear plaintext keys if successful
        if encrypted_count > 0:
            for wallet in unencrypted_wallets:
                if db.user_wallets.find_one({"_id": wallet.get('_id'), "encrypted_private_key": {"$ne": None}}):
                    db.user_wallets.update_one(
                        {"_id": wallet.get('_id')},
                        {"$set": {"private_key": None}}
                    )
        
        return jsonify({
            'success': True,
            'encrypted': encrypted_count,
            'failed': failed_count,
            'message': f'Successfully encrypted {encrypted_count} wallets'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/wallet/rotate-keys', methods=['POST'])
@jwt_required()
def rotate_encryption_keys():
    """Rotate encryption keys for all encrypted wallets"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get request data
        data = request.json
        reason = data.get('reason', 'Routine key rotation')
        new_master_key = data.get('new_master_key')
        
        if not new_master_key:
            return jsonify({'success': False, 'message': 'New master key is required'}), 400
        
        # Initialize encryption service
        from app.services.encryption_service import EncryptionService
        encryption_service = EncryptionService()
        
        # Start key rotation process
        rotation_id = encryption_service.rotate_encryption_key(new_master_key)
        
        if not rotation_id:
            return jsonify({'success': False, 'message': 'Key rotation failed'}), 500
        
        # Get the rotation record
        rotation = db.encryption_key_rotations.find_one({"_id": rotation_id})
        
        # Log the activity
        log = {
            "log_type": "key_rotation",
            "log_message": f"Admin {current_user_id} initiated key rotation. Reason: {reason}",
            "created_at": datetime.utcnow()
        }
        
        db.system_logs.insert_one(log)
        
        return jsonify({
            'success': True,
            'rotation_id': str(rotation_id),
            'wallets_updated': rotation.get('wallets_updated') if rotation else 0,
            'status': rotation.get('status') if rotation else 'unknown',
            'message': 'Encryption key rotation completed'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/wallet/access-logs', methods=['GET'])
@jwt_required()
def wallet_access_logs():
    """Get wallet key access logs"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Calculate skip for pagination
        skip = (page - 1) * per_page
        
        # Get access logs with pagination
        logs = list(db.wallet_key_access_logs.find().sort("accessed_at", -1).skip(skip).limit(per_page))
        total = db.wallet_key_access_logs.count_documents({})
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        # Format the logs
        formatted_logs = []
        for log in logs:
            # Get admin username
            admin_id = log.get('admin_id')
            if isinstance(admin_id, str) and ObjectId.is_valid(admin_id):
                admin_id = ObjectId(admin_id)
            admin = db.users.find_one({"_id": admin_id})
            admin_name = admin.get('user_name') if admin else "Unknown"
            
            # Get user username
            user_id = log.get('user_id')
            if isinstance(user_id, str) and ObjectId.is_valid(user_id):
                user_id = ObjectId(user_id)
            user = db.users.find_one({"_id": user_id})
            user_name = user.get('user_name') if user else "Unknown"
            
            formatted_logs.append({
                'id': str(log.get('_id')),
                'wallet_id': str(log.get('wallet_id')),
                'user_id': str(log.get('user_id')),
                'user_name': user_name,
                'admin_id': str(log.get('admin_id')),
                'admin_name': admin_name,
                'access_type': log.get('access_type'),
                'access_reason': log.get('access_reason'),
                'accessed_at': log.get('accessed_at').strftime('%Y-%m-%d %H:%M:%S') if log.get('accessed_at') else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'logs': formatted_logs,
            'total': total,
            'pages': total_pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/wallet/encrypt-single/<wallet_id>', methods=['POST'])
@jwt_required()
def encrypt_single_wallet(wallet_id):
    """Encrypt a single wallet's private key"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
            current_user_id = ObjectId(current_user_id)
        
        from app import db
        
        user = db.users.find_one({"_id": current_user_id})
        
        if not user or not user.get('is_admin'):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get request data
        data = request.json
        reason = data.get('reason', 'Manual single wallet encryption')
        
        # Get the wallet
        if ObjectId.is_valid(wallet_id):
            wallet_id = ObjectId(wallet_id)
        
        wallet = db.user_wallets.find_one({"_id": wallet_id})
        
        if not wallet:
            return jsonify({'success': False, 'message': 'Wallet not found'}), 404
        
        if not wallet.get('private_key') and not data.get('private_key'):
            return jsonify({'success': False, 'message': 'No private key available to encrypt'}), 400
        
        # Initialize encryption service
        from app.services.encryption_service import EncryptionService
        encryption_service = EncryptionService()
        
        # Use provided private key or existing one
        private_key = data.get('private_key') or wallet.get('private_key')
        
        # Get user_id from wallet
        user_id = wallet.get('user_id')
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_id = ObjectId(user_id)
        
        # Encrypt the private key
        encrypted_key = encryption_service.encrypt_private_key(
            private_key,
            user_id
        )
        
        if not encrypted_key:
            return jsonify({'success': False, 'message': 'Encryption failed'}), 500
        
        # Update wallet
        db.user_wallets.update_one(
            {"_id": wallet_id},
            {
                "$set": {
                    "encrypted_private_key": encrypted_key,
                    "encryption_version": "v1",
                    "key_encrypted_at": datetime.utcnow(),
                    "private_key": None if wallet.get('private_key') else wallet.get('private_key')
                }
            }
        )
        
        # Log access
        log = {
            "wallet_id": wallet_id,
            "user_id": user_id,
            "admin_id": current_user_id,
            "access_type": "encryption",
            "access_reason": reason,
            "accessed_at": datetime.utcnow()
        }
        
        # System log
        system_log = {
            "log_type": "wallet_encryption",
            "log_message": f"Admin {current_user_id} encrypted wallet {wallet_id}. Reason: {reason}",
            "created_at": datetime.utcnow()
        }
        
        db.wallet_key_access_logs.insert_one(log)
        db.system_logs.insert_one(system_log)
        
        return jsonify({
            'success': True,
            'wallet_id': str(wallet_id),
            'message': 'Wallet private key encrypted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500