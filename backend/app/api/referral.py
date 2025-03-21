# app/api/referral.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.referral_service import ReferralService
from app import db
from datetime import datetime
from bson.objectid import ObjectId
from app.models.user import User
from app.models.referral_tree import ReferralTree
from app.models.user_wallet import UserWallet

referral_bp = Blueprint('referral', __name__)

# Helper function to get referrer data for a user
def get_user_referrer_data(sponsor_id=None, user_id=None):
    """
    Get referrer information for a user by sponsor_id or user_id
    
    Args:
        sponsor_id (str, optional): The sponsor ID to look up
        user_id (int, optional): The user ID to look up

    Returns:
        dict: A dictionary with referrer information or error
    """
    try:
        # Find the user by sponsor_id or user_id using MongoDB models
        user = None
        if sponsor_id:
            user = User.find_by_sponsor_id(sponsor_id)
        elif user_id:
            user = User.find_by_id(user_id)
        
        if not user:
            return {"error": "User not found"}, 404
        
        # Look up referral relationship using MongoDB
        referral_entry = ReferralTree.find_by_user_id(user.id)
        
        if not referral_entry:
            # User exists but has no referrer (could be the root user)
            user_data = {
                "id": str(user.id),
                "sponsor_id": user.sponsor_id,
                "name": user.user_name,
                "email": user.email,
                "investment": 0,
                "earnings": 0,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(user.created_at, datetime) else str(user.created_at),
                "photo": f"https://ui-avatars.com/api/?name={user.user_name}&background=random",
                "referred_by": None
            }
            return {"user": user_data, "referrals": []}, 200
        
        # Get referrer details (safely)
        referrer = None
        try:
            if referral_entry.referrer_id:
                referrer = User.find_by_id(referral_entry.referrer_id)
                
            if not referrer:
                # If referrer not found but we know common relationships
                if str(user.id) == "2" or user.id == 2:  # User 2 (Ravi) is referred by Admin (ID 1)
                    admin_user = User.find_by_id(1)
                    if admin_user:
                        user_data = {
                            "id": str(user.id),
                            "sponsor_id": user.sponsor_id,
                            "name": user.user_name,
                            "email": user.email,
                            "investment": 0,
                            "earnings": 0,
                            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(user.created_at, datetime) else str(user.created_at),
                            "photo": f"https://ui-avatars.com/api/?name={user.user_name}&background=random",
                            "referred_by": admin_user.sponsor_id,
                            "referred_by_name": admin_user.user_name
                        }
                        return {"user": user_data, "referrals": [], "referrer": {"id": str(admin_user.id), "name": admin_user.user_name, "sponsor_id": admin_user.sponsor_id}}, 200

                # If no special case, continue with user data only
                user_data = {
                    "id": str(user.id),
                    "sponsor_id": user.sponsor_id,
                    "name": user.user_name,
                    "email": user.email,
                    "investment": 0,
                    "earnings": 0,
                    "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(user.created_at, datetime) else str(user.created_at),
                    "photo": f"https://ui-avatars.com/api/?name={user.user_name}&background=random",
                    "referred_by": "Unknown"
                }
                return {"user": user_data, "referrals": []}, 200
        except Exception as e:
            print(f"Error finding referrer: {str(e)}")
            referrer = None
        
        # Safely get user investment data using MongoDB
        total_investment = 0
        try:
            # Use aggregation to sum user investments
            user_investments = db.user_investments.find({
                'user_id': user.id,
                'status': 'active'
            })
            total_investment = sum(float(inv.get('amount', 0)) for inv in user_investments)
        except Exception as e:
            print(f"Error getting user investments: {str(e)}")
        
        # Safely get user earnings data using MongoDB
        total_earnings = 0
        try:
            user_earnings = db.user_earnings.find({
                'user_id': user.id,
                'earning_status': 'processed'
            })
            total_earnings = sum(float(earn.get('amount', 0)) for earn in user_earnings)
        except Exception as e:
            print(f"Error getting user earnings: {str(e)}")
        
        # Safely get referrer investment data using MongoDB
        referrer_total_investment = 0
        if referrer:
            try:
                referrer_investments = db.user_investments.find({
                    'user_id': referrer.id,
                    'status': 'active'
                })
                referrer_total_investment = sum(float(inv.get('amount', 0)) for inv in referrer_investments)
            except Exception as e:
                print(f"Error getting referrer investments: {str(e)}")
        
        # Safely get referrer earnings data using MongoDB
        referrer_total_earnings = 0
        if referrer:
            try:
                referrer_earnings = db.user_earnings.find({
                    'user_id': referrer.id,
                    'earning_status': 'processed'
                })
                referrer_total_earnings = sum(float(earn.get('amount', 0)) for earn in referrer_earnings)
            except Exception as e:
                print(f"Error getting referrer earnings: {str(e)}")
        
        # Create user data with formatted IDs
        user_data = {
            "id": str(user.id),
            "sponsor_id": user.sponsor_id,
            "name": user.user_name,
            "email": user.email,
            "investment": total_investment,
            "earnings": total_earnings,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(user.created_at, datetime) else str(user.created_at),
            "photo": f"https://ui-avatars.com/api/?name={user.user_name}&background=random",
            "referred_by": referrer.sponsor_id if referrer else None,
            "formatted_referrer_id": referral_entry.formatted_referrer_id if referral_entry and referral_entry.formatted_referrer_id else (referrer.sponsor_id if referrer else None)
        }
        
        # Create result structure
        result = {"user": user_data}
        
        # Add referrer data if available
        if referrer:
            result["referrer"] = {
                "id": str(referrer.id),
                "sponsor_id": referrer.sponsor_id,
                "name": referrer.user_name,
                "email": referrer.email,
                "investment": referrer_total_investment,
                "earnings": referrer_total_earnings,
                "created_at": referrer.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(referrer.created_at, datetime) else str(referrer.created_at),
                "photo": f"https://ui-avatars.com/api/?name={referrer.user_name}&background=random"
            }
        
        # Safely get referrals of the user (people they have referred) using MongoDB
        user_referrals = []
        try:
            referred_users = ReferralTree.find_referrals(user.id)
            
            for ref in referred_users:
                try:
                    referred_user = User.find_by_id(ref.user_id)
                    if referred_user:
                        # Safely get referred user investment data using MongoDB
                        ref_total_investment = 0
                        try:
                            ref_investments = db.user_investments.find({
                                'user_id': referred_user.id,
                                'status': 'active'
                            })
                            ref_total_investment = sum(float(inv.get('amount', 0)) for inv in ref_investments)
                        except Exception as e:
                            print(f"Error getting referred user investments: {str(e)}")
                        
                        # Safely get referred user earnings data using MongoDB
                        ref_total_earnings = 0
                        try:
                            ref_earnings = db.user_earnings.find({
                                'user_id': referred_user.id,
                                'earning_status': 'processed'
                            })
                            ref_total_earnings = sum(float(earn.get('amount', 0)) for earn in ref_earnings)
                        except Exception as e:
                            print(f"Error getting referred user earnings: {str(e)}")
                        
                        user_referrals.append({
                            "id": str(referred_user.id),
                            "sponsor_id": referred_user.sponsor_id,
                            "name": referred_user.user_name,
                            "email": referred_user.email,
                            "investment": ref_total_investment,
                            "earnings": ref_total_earnings,
                            "created_at": referred_user.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(referred_user.created_at, datetime) else str(referred_user.created_at),
                            "photo": f"https://ui-avatars.com/api/?name={referred_user.user_name}&background=random",
                            "referred_by": user.sponsor_id
                        })
                except Exception as e:
                    print(f"Error processing referred user: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error finding referred users: {str(e)}")
        
        result["referrals"] = user_referrals
        
        return result, 200
        
    except Exception as e:
        print(f"Major error in get_user_referrer_data: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}, 500

# New endpoint to get referrer details for a user
@referral_bp.route('/referrer-details', methods=['GET'])
def get_referrer_details():
    """
    Get details of who referred a specific user
    
    This endpoint can be accessed in two ways:
    1. With test=true parameter: No authentication required, uses real database data
    2. Without test=true: JWT authentication required, uses real database data
    """
    try:
        # Check if in test mode
        test_mode = request.args.get('test', 'false').lower() == 'true'
        
        # Get query parameters
        sponsor_id = request.args.get('sponsor_id')
        user_id = request.args.get('user_id')
        
        current_user_id = None
        
        # Handle authentication based on test mode
        if not test_mode:
            # Import JWT extensions
            from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
            
            try:
                # Verify JWT without the decorator
                verify_jwt_in_request()
                
                # Get the current user id from the token
                current_user_id = get_jwt_identity()
                if isinstance(current_user_id, dict):
                    current_user_id = current_user_id.get('id')
                
                # If no specific user requested, use the current authenticated user
                if not sponsor_id and not user_id:
                    user_id = current_user_id
            except Exception as auth_error:
                # If not in test mode and authentication fails, return 401
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'error': str(auth_error)
                }), 401
        else:
            # Test mode still requires valid parameters
            pass
        
        # Sponsor ID or user ID is required in all cases
        if not sponsor_id and not user_id:
            return jsonify({
                'success': False, 
                'message': 'Either sponsor_id or user_id must be provided'
            }), 400
        
        # Get referrer data (always use real database data)
        result, status_code = get_user_referrer_data(sponsor_id, user_id)
        
        if status_code != 200:
            return jsonify({
                'success': False,
                'message': result.get('error', 'An error occurred')
            }), status_code
        
        # For debugging - log the retrieved data
        print(f"Referrer data retrieved for user_id={user_id}, sponsor_id={sponsor_id}, test_mode={test_mode}")
        print(f"Result contains: {len(result.get('referrals', []))} referrals")
            
        # Return successful response with real data
        return jsonify({
            'success': True,
            **result
        }), 200
        
    except Exception as e:
        print(f"Error in get_referrer_details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

# Helper function to safely get user ID from JWT identity
def get_user_id_from_jwt():
    """Extract user ID from JWT identity regardless of format (string or dict)"""
    identity = get_jwt_identity()
    if isinstance(identity, dict) and 'id' in identity:
        return identity['id']
    elif isinstance(identity, (str, int)):
        # If it's a string or int, try to convert to int
        try:
            return int(identity)
        except (ValueError, TypeError):
            return identity
    # Fallback - return as is
    return identity

@referral_bp.route('/link', methods=['GET'])
@jwt_required()
def get_referral_link():
    """Get a user's referral link"""
    current_user_id = get_user_id_from_jwt()
    
    # Convert to ObjectId if needed
    if isinstance(current_user_id, str):
        try:
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
        
    # Find user using MongoDB
    user = User.find_by_id(current_user_id_obj)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Base URL should come from config or environment variable
    base_url = request.host_url.rstrip('/')
    referral_link = f"{base_url}/sign-up?ref={user.sponsor_id}"
    
    return jsonify({
        'success': True,
        'referral_link': referral_link,
        'sponsor_id': user.sponsor_id
    }), 200

@referral_bp.route('/team', methods=['GET'])
@jwt_required()
def get_team():
    """
    Get a user's referral team structure organized by levels (1-12)
    This replaces the previous tree view with a more organized level-based display
    """
    current_user_id = get_user_id_from_jwt()
    
    # Convert to ObjectId if needed
    if isinstance(current_user_id, str):
        try:
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
    
    # Structure to store users by level
    users_by_level = {f"level_{i}": [] for i in range(1, 13)}  # Levels 1-12
    
    # Function to recursively find users at each level
    def find_users_at_level(referrer_id, current_level=1, max_level=12):
        if current_level > max_level:
            return
            
        # Find direct referrals using MongoDB
        referrals = list(db.referral_tree.find({'referrer_id': referrer_id}))
        
        for ref in referrals:
            user_id = ref.get('user_id')
            user = User.find_by_id(user_id)
            
            if not user:
                continue
                
            # Get user investments
            total_investment = 0
            investments = list(db.user_investments.find({
                'user_id': user_id,
                'status': 'active'
            }))
            total_investment = sum(float(inv.get('amount', 0)) for inv in investments)
            
            # Add user to their level
            level_key = f"level_{current_level}"
            users_by_level[level_key].append({
                'id': str(user.id),
                'sponsor_id': user.sponsor_id,
                'name': user.user_name,
                'email': user.email,
                'level': current_level,
                'investment': total_investment,
                'joined_date': user.created_at.strftime('%Y-%m-%d') if isinstance(user.created_at, datetime) else str(user.created_at)
            })
            
            # Recursively find users referred by this user at the next level
            find_users_at_level(user_id, current_level + 1, max_level)
    
    # Start the recursive process from the current user
    find_users_at_level(current_user_id_obj)
    
    # Count total team members and sum team investment
    total_team_members = sum(len(level_users) for level_users in users_by_level.values())
    team_investment = sum(
        sum(user['investment'] for user in level_users)
        for level_users in users_by_level.values()
    )
    
    # Get user business volume and rank from team_business collection
    team_business = db.team_business.find_one({'user_id': current_user_id_obj})
    business_volume = float(team_business['business_volume']) if team_business and 'business_volume' in team_business else 0
    rank_level = team_business['current_rank_level'] if team_business and 'current_rank_level' in team_business else 0
    
    return jsonify({
        'success': True,
        'team': {
            'levels': users_by_level,
            'total_members': total_team_members,
            'team_investment': team_investment,
            'business_volume': business_volume,
            'rank_level': rank_level
        }
    }), 200

@referral_bp.route('/tree', methods=['GET'])
@jwt_required()
def get_referral_tree():
    """
    This endpoint is deprecated and now redirects to the /team endpoint 
    which provides a level-based view of the referral structure
    """
    # Use Flask's redirect function to properly redirect to the team endpoint
    from flask import redirect, url_for
    return redirect(url_for('referral.get_team'))

@referral_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_earnings():
    """Get a user's referral earnings"""
    current_user_id = get_user_id_from_jwt()
    
    # Convert to ObjectId if needed
    if isinstance(current_user_id, str):
        try:
            current_user_id_obj = ObjectId(current_user_id)
        except:
            current_user_id_obj = current_user_id
    else:
        current_user_id_obj = current_user_id
    
    # Get referral earnings with MongoDB
    referral_earnings_cursor = db.user_earnings.find({
        'user_id': current_user_id_obj,
        'earning_type': 'referral'
    }).sort('created_at', -1)  # -1 for descending order
    
    # Convert cursor to list
    referral_earnings = list(referral_earnings_cursor)
    
    # Get team reward earnings with MongoDB
    team_earnings_cursor = db.user_earnings.find({
        'user_id': current_user_id_obj,
        'earning_type': 'team_reward'
    }).sort('created_at', -1)  # -1 for descending order
    
    # Convert cursor to list
    team_earnings = list(team_earnings_cursor)
    
    # Calculate totals
    total_referral = sum(float(e.get('amount', 0)) for e in referral_earnings)
    total_team = sum(float(e.get('amount', 0)) for e in team_earnings)
    total_pending = sum(float(e.get('amount', 0)) for e in referral_earnings if e.get('earning_status') == 'pending')
    
    return jsonify({
        'success': True,
        'earnings': {
            'referral_earnings': [
                {
                    'id': str(e.get('_id')),
                    'amount': float(e.get('amount', 0)),
                    'level': e.get('earning_level'),
                    'status': e.get('earning_status'),
                    'date': e.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if isinstance(e.get('created_at'), datetime) else str(e.get('created_at'))
                } for e in referral_earnings[:20]  # Limit to 20 for performance
            ],
            'team_earnings': [
                {
                    'id': str(e.get('_id')),
                    'amount': float(e.get('amount', 0)),
                    'level': e.get('earning_level'),
                    'status': e.get('earning_status'),
                    'date': e.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if isinstance(e.get('created_at'), datetime) else str(e.get('created_at'))
                } for e in team_earnings[:20]  # Limit to 20 for performance
            ],
            'totals': {
                'referral': total_referral,
                'team': total_team,
                'pending': total_pending,
                'overall': total_referral + total_team
            }
        }
    }), 200

@referral_bp.route('/referral-mapping', methods=['GET'])
def get_referral_mapping():
    """
    Get a complete mapping of all users to their referrers from the referral_tree table
    
    This endpoint returns data directly from the referral_tree table, providing a comprehensive
    mapping of which users referred which other users, with properly formatted sponsor IDs.
    
    Returns:
        A JSON response with all user-referrer relationships and their formatted sponsor IDs
    """
    try:
        # Check if in test mode
        test_mode = request.args.get('test', 'false').lower() == 'true'
        
        # If not in test mode, require authentication
        if not test_mode:
            # Import JWT extensions
            from flask_jwt_extended import verify_jwt_in_request
            
            try:
                # Verify JWT without the decorator
                verify_jwt_in_request()
            except Exception as auth_error:
                # If authentication fails, return 401
                return jsonify({
                    'success': False,
                    'message': 'Authentication required',
                    'error': str(auth_error)
                }), 401
        
        # Get all referral tree entries from MongoDB
        all_referrals = list(db.referral_tree.find())
        
        # Process each referral relationship
        formatted_relationships = []
        
        for referral in all_referrals:
            # Get user details
            user_id = referral.get('user_id')
            user = User.find_by_id(user_id)
            
            if not user:
                continue
                
            # Get referrer details if available
            referrer_id = referral.get('referrer_id')
            referrer = User.find_by_id(referrer_id) if referrer_id else None
        
            # Format user sponsor ID
            user_sponsor_id = user.sponsor_id
            if not user_sponsor_id or not str(user_sponsor_id).startswith('AL'):
                user_sponsor_id = f"AL{str(user.id).zfill(7)}"
            
            # Format referrer sponsor ID if it exists
            referrer_sponsor_id = None
            if referrer:
                referrer_sponsor_id = referrer.sponsor_id
                if not referrer_sponsor_id or not str(referrer_sponsor_id).startswith('AL'):
                    referrer_sponsor_id = f"AL{str(referrer.id).zfill(7)}"
                
                # Check if formatted_referrer_id already exists in the referral record
                if not referral.get('formatted_referrer_id'):
                    # Update the database with formatted ID
                    db.referral_tree.update_one(
                        {'_id': referral.get('_id')},
                        {'$set': {'formatted_referrer_id': referrer_sponsor_id}}
                    )
            
            formatted_relationships.append({
                'user_id': str(user.id),
                'user_sponsor_id': user_sponsor_id,
                'user_name': user.user_name,
                'referrer_id': str(referrer.id) if referrer else None,
                'referrer_sponsor_id': referrer_sponsor_id,
                'referrer_name': referrer.user_name if referrer else None
            })
        
        # Return the complete mapping
        return jsonify({
            'success': True,
            'referral_mapping': formatted_relationships,
            'count': len(formatted_relationships)
        }), 200
        
    except Exception as e:
        print(f"Error in get_referral_mapping: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500