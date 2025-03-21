# app/api/token.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.token_service import TokenService
from app import db
from bson.objectid import ObjectId
from datetime import datetime

token_bp = Blueprint('token', __name__)
token_service = TokenService()

@token_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_token_balance():
    """Get a user's LOOP token balance"""
    current_user_id = get_jwt_identity()['id']
    
    # Convert to ObjectId if string
    if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
        current_user_id = ObjectId(current_user_id)
    
    # Find user wallet in MongoDB
    wallet = db.user_wallets.find_one({"user_id": current_user_id})
    
    if not wallet:
        return jsonify({'success': False, 'message': 'No wallet found for this user'}), 404
    
    balance = token_service.get_loop_token_balance(wallet.get('deposit_address'))
    
    return jsonify({
        'success': True,
        'token_balance': balance,
        'wallet_address': wallet.get('deposit_address')
    }), 200

@token_bp.route('/market', methods=['GET'])
def get_token_market_info():
    """Get LOOP token market information from PancakeSwap"""
    market_data = token_service.get_pancakeswap_data()
    
    if not market_data:
        return jsonify({'success': False, 'message': 'Unable to fetch market data'}), 500
    
    return jsonify({
        'success': True,
        'market_data': market_data
    }), 200

@token_bp.route('/airdrop/request', methods=['POST'])
@jwt_required()
def request_airdrop():
    """Request LOOP token airdrop for social media activity"""
    current_user_id = get_jwt_identity()['id']
    data = request.get_json()
    
    if 'activity_type' not in data or 'proof_url' not in data:
        return jsonify({'success': False, 'message': 'Missing activity type or proof URL'}), 400
    
    activity_type = data['activity_type']
    proof_url = data['proof_url']
    
    # Validate activity type
    valid_types = ['twitter_share', 'facebook_post', 'blog_article', 'youtube_video']
    if activity_type not in valid_types:
        return jsonify({'success': False, 'message': 'Invalid activity type'}), 400
    
    # Convert to ObjectId if string
    if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
        current_user_id = ObjectId(current_user_id)
    
    # Get user and wallet from MongoDB
    user = db.users.find_one({"_id": current_user_id})
    wallet = db.user_wallets.find_one({"user_id": current_user_id})
    
    if not wallet:
        return jsonify({'success': False, 'message': 'No wallet found for this user'}), 404
    
    # Determine airdrop amount based on activity type
    amounts = {
        'twitter_share': 5,
        'facebook_post': 5,
        'blog_article': 20,
        'youtube_video': 50
    }
    
    airdrop_amount = amounts.get(activity_type, 5)
    
    # Check if user already has a pending request
    existing_request = db.token_airdrops.find_one({
        "user_id": current_user_id,
        "status": "pending"
    })
    
    if existing_request:
        return jsonify({
            'success': False, 
            'message': 'You already have a pending airdrop request'
        }), 400
    
    # Create airdrop request document
    airdrop = {
        "user_id": current_user_id,
        "wallet_address": wallet.get('deposit_address'),
        "amount": airdrop_amount,
        "status": "pending",
        "airdrop_type": "social_media",
        "reason": f"{activity_type}: {proof_url}",
        "created_at": datetime.utcnow()
    }
    
    # Insert into MongoDB
    result = db.token_airdrops.insert_one(airdrop)
    airdrop_id = result.inserted_id
    
    return jsonify({
        'success': True,
        'message': 'Airdrop request submitted for review',
        'request_id': str(airdrop_id),
        'amount': airdrop_amount
    }), 201

@token_bp.route('/airdrop/admin/approve/<request_id>', methods=['POST'])
@jwt_required()
def approve_airdrop(request_id):
    """Admin endpoint to approve and process an airdrop request"""
    current_user_id = get_jwt_identity()['id']
    
    # Convert to ObjectId if string
    if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
        current_user_id = ObjectId(current_user_id)
    
    # Convert request_id to ObjectId if valid
    if ObjectId.is_valid(request_id):
        request_id = ObjectId(request_id)
    
    # Check if user is admin
    user = db.users.find_one({"_id": current_user_id})
    
    if not user or not user.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get the airdrop request
    airdrop = db.token_airdrops.find_one({"_id": request_id})
    
    if not airdrop:
        return jsonify({'success': False, 'message': 'Airdrop request not found'}), 404
    
    if airdrop.get('status') != 'pending':
        return jsonify({'success': False, 'message': f'Request is already {airdrop.get("status")}'}, 400)
    
    # Process the airdrop
    success, result = token_service.airdrop_tokens(airdrop.get('wallet_address'), airdrop.get('amount'))
    
    if not success:
        return jsonify({'success': False, 'message': result}), 500
    
    return jsonify({
        'success': True,
        'message': 'Airdrop processed successfully',
        'transaction_id': result
    }), 200

@token_bp.route('/airdrop/history', methods=['GET'])
@jwt_required()
def get_airdrop_history():
    """Get a user's airdrop history"""
    current_user_id = get_jwt_identity()['id']
    
    # Convert to ObjectId if string
    if isinstance(current_user_id, str) and ObjectId.is_valid(current_user_id):
        current_user_id = ObjectId(current_user_id)
    
    # Query MongoDB for user's airdrops, sorted by created_at descending
    airdrops = list(db.token_airdrops.find(
        {"user_id": current_user_id}
    ).sort("created_at", -1))
    
    # Convert ObjectId to string for JSON serialization
    for airdrop in airdrops:
        if '_id' in airdrop:
            airdrop['_id'] = str(airdrop['_id'])
        if 'user_id' in airdrop and isinstance(airdrop['user_id'], ObjectId):
            airdrop['user_id'] = str(airdrop['user_id'])
        # Convert datetime objects to strings
        for key, value in airdrop.items():
            if isinstance(value, datetime):
                airdrop[key] = value.isoformat()
    
    return jsonify({
        'success': True,
        'airdrops': airdrops
    }), 200