# app/api/dashboard.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

def get_user_id_from_jwt():
    """
    Helper function to extract user ID from JWT identity regardless of format
    Handles both string IDs and dictionary format {'id': user_id}
    """
    identity = get_jwt_identity()
    if isinstance(identity, dict) and 'id' in identity:
        return identity['id']
    return identity  # Assume the identity itself is the user ID

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """Get user dashboard summary"""
    current_user_id = get_user_id_from_jwt()
    
    # Try to convert to ObjectId if it's a string
    if isinstance(current_user_id, str):
        try:
            from bson.objectid import ObjectId
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
    
    # Get user info using MongoDB
    from app.models.user import User
    user = User.find_by_id(current_user_id_obj)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get active investments using MongoDB
    active_investments_cursor = db.user_investments.find({
        'user_id': current_user_id_obj,
        'investment_status': 'active'
    })
    active_investments = len(list(active_investments_cursor))
    
    # Get earnings using MongoDB aggregation
    total_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    total_earnings_result = list(db.user_earnings.aggregate(total_earnings_pipeline))
    total_earnings = float(total_earnings_result[0]['total']) if total_earnings_result else 0
    
    # Get referral count using MongoDB
    referral_count_cursor = db.referral_tree.find({'referrer_id': current_user_id_obj})
    referral_count = len(list(referral_count_cursor))
    
    # Get current bid cycle using MongoDB
    current_cycle = db.bid_cycles.find_one({'cycle_status': 'open'})
    if not current_cycle:
        current_cycle = db.bid_cycles.find_one(
            {'cycle_status': 'pending'},
            sort=[('_id', -1)]  # Sort by _id descending for latest
        )
    
    return jsonify({
        'success': True,
        'dashboard': {
            'user': {
                'id': str(user.id),
                'name': user.user_name,
                'balance': float(user.balance) if hasattr(user, 'balance') else 0,
                'sponsor_id': user.sponsor_id
            },
            'active_investments': active_investments,
            'total_earnings': float(total_earnings),
            'referral_count': referral_count,
            'cycle': {
                'id': str(current_cycle['_id']) if current_cycle else None,
                'status': current_cycle['cycle_status'] if current_cycle else None,
                'remaining_units': (current_cycle['total_bids_allowed'] - current_cycle['bids_filled']) if current_cycle else 0,
                'open_time': current_cycle['open_time'].strftime('%Y-%m-%d %H:%M:%S') if current_cycle and 'open_time' in current_cycle else None
            }
        }
    }), 200

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get user dashboard statistics"""
    current_user_id = get_user_id_from_jwt()
    
    # Try to convert to ObjectId if it's a string
    if isinstance(current_user_id, str):
        try:
            from bson.objectid import ObjectId
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
    
    # Get investment stats using MongoDB aggregation
    total_invested_pipeline = [
        {'$match': {'user_id': current_user_id_obj}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    total_invested_result = list(db.user_investments.aggregate(total_invested_pipeline))
    total_invested = float(total_invested_result[0]['total']) if total_invested_result else 0
    
    # Get earnings breakdown using MongoDB
    referral_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj, 'earning_type': 'referral'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    referral_earnings_result = list(db.user_earnings.aggregate(referral_earnings_pipeline))
    referral_earnings = float(referral_earnings_result[0]['total']) if referral_earnings_result else 0
    
    daily_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj, 'earning_type': 'daily'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    daily_earnings_result = list(db.user_earnings.aggregate(daily_earnings_pipeline))
    daily_earnings = float(daily_earnings_result[0]['total']) if daily_earnings_result else 0
    
    team_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj, 'earning_type': 'team_reward'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    team_earnings_result = list(db.user_earnings.aggregate(team_earnings_pipeline))
    team_earnings = float(team_earnings_result[0]['total']) if team_earnings_result else 0
    
    return jsonify({
        'success': True,
        'stats': {
            'total_invested': float(total_invested),
            'earnings': {
                'referral': float(referral_earnings),
                'daily': float(daily_earnings),
                'team': float(team_earnings),
                'total': float(referral_earnings + daily_earnings + team_earnings)
            }
        }
    }), 200

# Create a separate endpoint for OPTIONS preflight requests to handle CORS
@dashboard_bp.route('/earnings', methods=['OPTIONS'])
def earnings_options():
    """Handle OPTIONS request for /earnings endpoint (CORS preflight)"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response, 200

@dashboard_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_earnings_breakdown():
    """Get user earnings breakdown"""
    current_user_id = get_user_id_from_jwt()
    
    # Try to convert to ObjectId if it's a string
    if isinstance(current_user_id, str):
        try:
            from bson.objectid import ObjectId
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
    
    # Get earnings breakdown using MongoDB
    referral_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj, 'earning_type': 'referral'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    referral_earnings_result = list(db.user_earnings.aggregate(referral_earnings_pipeline))
    referral_earnings = float(referral_earnings_result[0]['total']) if referral_earnings_result else 0
    
    daily_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj, 'earning_type': 'daily'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    daily_earnings_result = list(db.user_earnings.aggregate(daily_earnings_pipeline))
    daily_earnings = float(daily_earnings_result[0]['total']) if daily_earnings_result else 0
    
    team_earnings_pipeline = [
        {'$match': {'user_id': current_user_id_obj, 'earning_type': 'team_reward'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    team_earnings_result = list(db.user_earnings.aggregate(team_earnings_pipeline))
    team_earnings = float(team_earnings_result[0]['total']) if team_earnings_result else 0
    
    # Create response with CORS headers
    response = jsonify({
        'success': True,
        'earnings': {
            'referral': float(referral_earnings),
            'daily': float(daily_earnings),
            'team': float(team_earnings),
            'total': float(referral_earnings + daily_earnings + team_earnings)
        }
    })
    
    # Add CORS headers to GET response too
    response.headers.add('Access-Control-Allow-Origin', '*')
    
    return response, 200

# Create a separate endpoint for OPTIONS preflight requests to handle CORS
@dashboard_bp.route('/top-earners', methods=['OPTIONS'])
def top_earners_options():
    """Handle OPTIONS request for /top-earners endpoint (CORS preflight)"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
    return response, 200

@dashboard_bp.route('/top-earners', methods=['GET'])
@jwt_required()
def get_top_earners():
    """Get top earners data, limited by the limit parameter"""
    # Get the limit parameter, defaulting to 5
    limit = request.args.get('limit', default=5, type=int)
    
    current_user_id = get_user_id_from_jwt()
    
    # Try to convert to ObjectId if it's a string
    if isinstance(current_user_id, str):
        try:
            from bson.objectid import ObjectId
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
    
    # Get top earners by aggregating total earnings per user
    # and sorting by total earnings in descending order
    pipeline = [
        {'$group': {
            '_id': '$user_id',
            'total_earnings': {'$sum': '$amount'}
        }},
        {'$sort': {'total_earnings': -1}},  # Sort by earnings descending
        {'$limit': limit}
    ]
    
    top_earners_result = list(db.user_earnings.aggregate(pipeline))
    
    # Fetch user details for each top earner
    from app.models.user import User
    top_earners = []
    
    for earner in top_earners_result:
        user_id = earner['_id']
        user = User.find_by_id(user_id)
        
        if user:
            top_earners.append({
                'user_id': str(user_id),
                'name': user.user_name if hasattr(user, 'user_name') else 'Anonymous',
                'sponsor_id': user.sponsor_id if hasattr(user, 'sponsor_id') else None,
                'total_earnings': float(earner['total_earnings'])
            })
    
    # Create response with CORS headers
    response = jsonify({
        'success': True,
        'top_earners': top_earners
    })
    
    # Add CORS headers to GET response too
    response.headers.add('Access-Control-Allow-Origin', '*')
    
    return response, 200