# app/api/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.services.auth_service import AuthService
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    required_fields = ['user_name', 'email', 'wallet_address', 'pin']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    # Check if wallet address or email already exists using MongoDB
    existing_wallet = db.users.find_one({"wallet_address": data['wallet_address']})
    if existing_wallet:
        return jsonify({'success': False, 'message': 'Wallet address already registered'}), 400
    
    existing_email = db.users.find_one({"email": data['email']})
    if existing_email:
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    # Generate unique sponsor ID using MongoDB
    counter_doc = db.sponsor_id_counter.find_one()
    if not counter_doc:
        # Create counter if it doesn't exist
        counter_doc = {
            "current_value": 1,
            "prefix": "AL"
        }
        db.sponsor_id_counter.insert_one(counter_doc)
    else:
        # Update counter atomically
        result = db.sponsor_id_counter.find_one_and_update(
            {"_id": counter_doc["_id"]},
            {"$inc": {"current_value": 1}},
            return_document=True
        )
        counter_doc = result
    
    sponsor_id = f"{counter_doc.get('prefix', 'AL')}{counter_doc.get('current_value', 1):07d}"
    
    # Process referrer information first if provided
    referrer_id = data.get('referrer_id')
    referrer = None
    
    if referrer_id:
        # Find referrer by sponsor ID in MongoDB
        referrer_doc = db.users.find_one({"sponsor_id": referrer_id})
        if referrer_doc:
            referrer = referrer_doc
            print(f"Found referrer: {referrer_doc.get('user_name')} (ID: {referrer_doc.get('_id')})")
    
    # Use the wallet address provided by the user during registration
    # This preserves their original web3 wallet connection
    
    # Create and encrypt the PIN
    from app.models.user import User
    user_obj = User()  # Temporary object just for pin hashing
    user_obj.set_pin(data['pin'])
    
    # Create user document for MongoDB with all fields initialized
    now = datetime.utcnow()
    user_doc = {
        "sponsor_id": sponsor_id,
        "user_name": data['user_name'],
        "email": data['email'],
        "wallet_address": data['wallet_address'],  # Use the user's provided wallet address
        "security_pin": user_obj.security_pin,
        "balance": 0.00,
        "is_active": True,
        "is_admin": False,
        "created_at": now,
        "updated_at": now,
        # Social media profiles initialized with empty values
        "facebook_profile": "",
        "twitter_profile": "",
        "instagram_profile": "",
        "profile_image": None,
        # Store referrer ID directly in user document for easier access
        "referred_by": referrer.get("sponsor_id") if referrer else None
    }
    
    # Insert user into MongoDB
    result = db.users.insert_one(user_doc)
    user_id = result.inserted_id
    
    if referrer:
        referrer_id_obj = referrer.get("_id")
        print(f"Creating referral relationship: user {user_id} referred by {referrer_id_obj}")
    
    # Create complete referral tree entry
    referral_doc = {
        "user_id": user_id,
        "referrer_id": referrer.get("_id") if referrer else None,
        "sponsor_id": sponsor_id,
        "referrer_sponsor_id": referrer.get("sponsor_id") if referrer else None,
        "tree_level": 1 if referrer else 0,
        "tree_position": 0,
        "created_at": now,
        "updated_at": now
    }
    db.referral_tree.insert_one(referral_doc)
    
    # Create user legs entry
    legs_doc = {
        "user_id": user_id,
        "total_legs": 0,
        "active_legs": 0,
        "created_at": now,
        "updated_at": now
    }
    db.user_legs.insert_one(legs_doc)
    
    # Update referrer's legs count if applicable
    if referrer_id and referrer:
        referrer_id_obj = referrer.get("_id")
        db.user_legs.update_one(
            {"user_id": referrer_id_obj},
            {"$inc": {"total_legs": 1, "active_legs": 1}}
        )
    
    # Generate Tatum.io wallet for new user automatically with retry mechanism
    # Using TatumHybridService which properly implements v3 for wallet generation
    from app.services.tatum_hybrid_service import TatumHybridService
    tatum_service = TatumHybridService()
    
    # Function to create wallet with retry logic and update user record
    def create_wallet_with_retry(user_id, max_retries=3):
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Attempt {attempt}/{max_retries} - Generating Tatum.io wallet for new user {user_id}")
                wallet, error = tatum_service.generate_wallet(user_id)
                
                if error:
                    print(f"Error generating wallet (attempt {attempt}): {error}")
                    if attempt < max_retries:
                        import time
                        time.sleep(1)  # Short delay before retry
                        continue
                    
                    # Log the final failure
                    log_doc = {
                        "log_type": "wallet_generation_error",
                        "log_message": f"Failed to generate wallet for new user {user_id} after {max_retries} attempts: {error}",
                        "created_at": datetime.utcnow()
                    }
                    db.system_logs.insert_one(log_doc)
                    return None
                else:
                    print(f"Successfully generated wallet {wallet.deposit_address} for user {user_id}")
                    
                    # Verify wallet was created properly - no need to create another one since
                    # tatum_hybrid_service.generate_wallet() already creates the wallet in database
                    saved_wallet = db.user_wallets.find_one({"user_id": user_id})
                    if not saved_wallet:
                        print(f"WARNING: UserWallet record not found after creation - check TatumHybridService")
                    
                    # Do NOT update the User's wallet_address to match the Tatum wallet
                    # We want to preserve the original web3 wallet address used for registration
                    # The Tatum wallet is stored in user_wallets collection for internal operations only
                    
                    # Verify that the user's original wallet address is still intact
                    verification_user = db.users.find_one({"_id": user_id})
                    if verification_user:
                        print(f"Verified user.wallet_address remains: {verification_user.get('wallet_address')}")
                    
                    # Log success
                    log_doc = {
                        "log_type": "wallet_generation",
                        "log_message": f"Generated wallet {wallet.deposit_address} for new user {user_id}",
                        "created_at": datetime.utcnow()
                    }
                    db.system_logs.insert_one(log_doc)
                    
                    # Do a final verification query to confirm success
                    verification = db.user_wallets.find_one({"user_id": user_id})
                    if verification:
                        print(f"Verified UserWallet record exists with deposit_address: {verification.get('deposit_address')}")
                    else:
                        print("WARNING: Final verification failed - UserWallet record still not found!")
                    
                    return wallet
            except Exception as e:
                print(f"Exception during wallet generation (attempt {attempt}): {str(e)}")
                if attempt < max_retries:
                    import time
                    time.sleep(1)  # Short delay before retry
                    continue
                
                # Log the final failure
                log_doc = {
                    "log_type": "wallet_generation_error",
                    "log_message": f"Exception during wallet generation for user {user_id} after {max_retries} attempts: {str(e)}",
                    "created_at": datetime.utcnow()
                }
                db.system_logs.insert_one(log_doc)
                return None
        return None
    
    # Create wallet with retry
    wallet = create_wallet_with_retry(user_id)
    
    # Only proceed if we successfully created a wallet
    if not wallet:
        # Delete the user and related records if wallet generation fails
        db.users.delete_one({"_id": user_id})
        db.referral_tree.delete_one({"user_id": user_id})
        db.user_legs.delete_one({"user_id": user_id})
        
        # Revert the referrer's legs count if applicable
        if referrer_id and referrer:
            referrer_id_obj = referrer.get("_id")
            db.user_legs.update_one(
                {"user_id": referrer_id_obj},
                {"$inc": {"total_legs": -1, "active_legs": -1}}
            )
        
        return jsonify({
            'success': False, 
            'message': 'Registration failed: Could not generate Tatum.io wallet. Please try again.'
        }), 500
    
    # Record activity now that we have the final wallet address
    activity_doc = {
        "user_id": user_id,
        "activity_type": "registration",
        "activity_description": "User created account",
        "ip_address": request.remote_addr,
        "created_at": datetime.utcnow()
    }
    db.user_activities.insert_one(activity_doc)
    
    # Create system log
    log_doc = {
        "log_type": "user_registration",
        "log_message": f"New user registered: {data['user_name']} ({data['email']}) with wallet {wallet.deposit_address}",
        "created_at": datetime.utcnow()
    }
    db.system_logs.insert_one(log_doc)
    
    # Get the updated user document
    updated_user_doc = db.users.find_one({"_id": user_id})
    
    # Convert to User object for token generation and response
    from app.models.user import User
    user = User.from_dict(updated_user_doc)
    
    # Generate token
    token = auth_service.generate_token(user)
    
    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'token': token,
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if 'wallet_address' not in data or 'pin' not in data:
        return jsonify({'success': False, 'message': 'Missing wallet_address or PIN'}), 400
    
    # Record login attempt
    now = datetime.utcnow()
    login_attempt = {
        "wallet_address": data['wallet_address'],
        "ip_address": request.remote_addr,
        "is_successful": False,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        # Insert login attempt
        db.login_attempts.insert_one(login_attempt)
        
        # Find user with wallet address - with various matching strategies
        wallet_address = data['wallet_address'].strip()
        user_doc = None
        
        print(f"Looking up user with wallet address: {wallet_address}")
        
        # Try simple exact match first
        user_doc = db.users.find_one({"wallet_address": wallet_address})
        
        # If not found, try case variants and prefixes
        if not user_doc:
            # Try lowercase
            user_doc = db.users.find_one({"wallet_address": wallet_address.lower()})
            
            # Try without 0x prefix if it exists
            if not user_doc and wallet_address.startswith('0x'):
                user_doc = db.users.find_one({"wallet_address": wallet_address[2:]})
            
            # Try with 0x prefix if it doesn't exist
            if not user_doc and not wallet_address.startswith('0x'):
                user_doc = db.users.find_one({"wallet_address": f"0x{wallet_address}"})
            
        # Debug results after all lookup attempts
        if user_doc:
            print("\nSUCCESS: Found matching user!")
            print(f"Found wallet address: '{user_doc.get('wallet_address')}'")
            print(f"Input wallet address: '{wallet_address}'")
            print(f"User ID: {user_doc.get('_id')}")
            print(f"Username: {user_doc.get('user_name')}")
        else:
            print("\nFAILURE: No matching user found after all attempts")
            print("=" * 50)
            # Return error response when no user is found
            return jsonify({'success': False, 'message': 'Invalid wallet address or PIN'}), 401
            
        # User found - convert document to User model for PIN checking
        from app.models.user import User
        user = User.from_dict(user_doc)
        print(f"User object created from document: {user is not None}")
        print(f"User ID: {user.id if user else 'None'}")
        
        # Check if user conversion failed
        if not user:
            print("User conversion failed")
            return jsonify({'success': False, 'message': 'Invalid wallet address or PIN'}), 401
        
        # Enhanced PIN verification with debug logging
        pin_match = user.check_pin(data['pin'])
        print(f"PIN check result: {pin_match}")
        
        if not pin_match:
            print("PIN verification failed")
            return jsonify({'success': False, 'message': 'Invalid wallet address or PIN'}), 401
        
        # PIN verification successful - update login attempt as successful
        db.login_attempts.update_one(
            {"wallet_address": data['wallet_address'], "created_at": now},
            {"$set": {"is_successful": True, "updated_at": datetime.utcnow()}}
        )
        
        # Record user activity using MongoDB
        activity = {
            "user_id": user.id,
            "activity_type": "login",
            "activity_description": "User logged in successfully",
            "ip_address": request.remote_addr,
            "created_at": datetime.utcnow()
        }
        db.user_activities.insert_one(activity)
        
        # Generate JWT token
        token = auth_service.generate_token(user)
        
        # Return successful login response
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Login error: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        # Get user ID from token (now as a string)
        user_id_str = get_jwt_identity()
        
        # Add detailed logging
        print(f"Profile request with identity: {user_id_str} (type: {type(user_id_str)})")
        
        try:
            # Try to parse as integer first (for backward compatibility)
            user_id = int(user_id_str)
        except ValueError:
            # If not an integer, it might be an ObjectId string
            from bson import ObjectId
            try:
                user_id = ObjectId(user_id_str)
            except:
                user_id = user_id_str  # Keep as string if conversion fails
        
        print(f"Looking up user with ID: {user_id} (type: {type(user_id)})")
        
        # Get the user from MongoDB
        user_doc = db.users.find_one({"_id": user_id})
        
        # If not found by _id, try by string representation or sponsor_id
        if not user_doc:
            print(f"User not found by _id, trying alternative lookups")
            # Try by string id
            user_doc = db.users.find_one({"id": str(user_id)})
            
            # Try by sponsor_id
            if not user_doc and isinstance(user_id_str, str):
                user_doc = db.users.find_one({"sponsor_id": user_id_str})
        
        if not user_doc:
            print(f"User not found for ID: {user_id}")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Convert document to User model
        from app.models.user import User
        user = User.from_dict(user_doc)
        
        # Make sure social media fields are included in the response
        user_dict = user.to_dict()
        
        # Add default values for missing social media fields
        # This ensures the frontend always gets these fields even if they're not in the database
        if 'facebook_profile' not in user_dict:
            user_dict['facebook_profile'] = ""
        if 'twitter_profile' not in user_dict:
            user_dict['twitter_profile'] = ""  
        if 'instagram_profile' not in user_dict:
            user_dict['instagram_profile'] = ""
            
        return jsonify({
            'success': True,
            'user': user_dict
        }), 200
    except Exception as e:
        print(f"Error in profile: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f"Profile error: {str(e)}"}), 500

@auth_bp.route('/test-auth', methods=['GET'])
@jwt_required()
def test_auth():
    """Simple endpoint to test if JWT authentication is working"""
    try:
        # Get the identity and print it for debugging
        identity = get_jwt_identity()
        print(f"JWT identity in test: {identity}")
        
        return jsonify({
            'success': True,
            'message': 'JWT authentication working correctly',
            'identity': identity
        }), 200
    except Exception as e:
        print(f"JWT test error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@auth_bp.route('/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update user profile information"""
    try:
        # Get user ID from token
        user_id = get_jwt_identity()
        
        print(f"DEBUG - Profile update request for user: {user_id}")
        print(f"DEBUG - Request data: {request.get_json()}")
        
        # Convert to ObjectId if needed
        if isinstance(user_id, str):
            try:
                from bson.objectid import ObjectId
                user_id = ObjectId(user_id)
                print(f"DEBUG - Converted user_id to ObjectId: {user_id}")
            except Exception as e:
                print(f"DEBUG - Failed to convert to ObjectId: {str(e)}")
                pass  # Continue with string ID
        
        # Get the user
        from app.models.user import User
        user = User.find_by_id(user_id)
        
        if not user:
            print(f"DEBUG - User not found for ID: {user_id}")
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        print(f"DEBUG - Found user: {user.user_name} (ID: {user.id})")
        
        # Get request data
        data = request.get_json()
        if not data:
            print("DEBUG - No JSON data in request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Update user information
        if 'name' in data and data['name']:
            print(f"DEBUG - Updating name from '{user.user_name}' to '{data['name']}'")
            user.user_name = data['name']
        
        if 'email' in data and data['email']:
            # Check if email already exists for another user
            existing_user = User.find_by_email(data['email'])
            if existing_user and str(existing_user.id) != str(user.id):
                print(f"DEBUG - Email {data['email']} already in use by user {existing_user.id}")
                return jsonify({'success': False, 'message': 'Email already in use'}), 400
            
            print(f"DEBUG - Updating email from '{user.email}' to '{data['email']}'")
            user.email = data['email']
        
        # Update social media links
        if 'social' in data:
            social = data['social']
            print(f"DEBUG - Social media data: {social}")
            
            if social.get('facebook') is not None:  # Allow empty string
                old_value = getattr(user, 'facebook_profile', '')
                print(f"DEBUG - Updating Facebook from '{old_value}' to '{social['facebook']}'")
                user.facebook_profile = social['facebook']
            
            if social.get('twitter') is not None:  # Allow empty string
                old_value = getattr(user, 'twitter_profile', '')
                print(f"DEBUG - Updating Twitter from '{old_value}' to '{social['twitter']}'")
                user.twitter_profile = social['twitter']
                
            if social.get('instagram') is not None:  # Allow empty string
                old_value = getattr(user, 'instagram_profile', '')
                print(f"DEBUG - Updating Instagram from '{old_value}' to '{social['instagram']}'")
                user.instagram_profile = social['instagram']
        
        print("DEBUG - Saving user changes to database")
        # Save changes
        try:
            save_result = user.save()
            print(f"DEBUG - Save result: {save_result}")
            
            if save_result:
                user_dict = user.to_dict()
                print(f"DEBUG - Updated user data: {user_dict}")
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'user': user_dict
                }), 200
            else:
                print("DEBUG - user.save() returned False")
                return jsonify({'success': False, 'message': 'Failed to update profile - database error'}), 500
        except Exception as save_error:
            print(f"DEBUG - Error in save() method: {str(save_error)}")
            import traceback
            print(traceback.format_exc())
            return jsonify({'success': False, 'message': f'Database save error: {str(save_error)}'}), 500
    
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Profile update error: {str(e)}'}), 500

@auth_bp.route('/user/profile-picture', methods=['POST'])
@jwt_required()
def update_profile_picture():
    """Update user profile picture"""
    try:
        # Get user ID from token
        user_id = get_jwt_identity()
        
        # Convert to ObjectId if needed
        if isinstance(user_id, str):
            try:
                from bson.objectid import ObjectId
                user_id = ObjectId(user_id)
            except:
                pass
        
        # Get the user
        from app.models.user import User
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if file is included in the request
        if 'profileImage' not in request.files:
            return jsonify({'success': False, 'message': 'No profile image provided'}), 400
        
        file = request.files['profileImage']
        
        # Check if file has a name (is valid)
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # In production, upload to a storage service (S3, Google Cloud Storage, etc.)
        # For this implementation, save the image as base64 in the database
        
        import base64
        from io import BytesIO
        
        # Read the file into memory
        file_bytes = BytesIO()
        file.save(file_bytes)
        file_bytes.seek(0)
        
        # Convert to base64
        encoded_image = base64.b64encode(file_bytes.read()).decode('utf-8')
        
        # Save with data URI scheme for direct embedding in HTML/CSS
        file_type = file.content_type or 'image/jpeg'  # Default to jpeg if content type is not provided
        data_uri = f"data:{file_type};base64,{encoded_image}"
        
        # Update user profile picture
        user.profile_image = data_uri
        
        # Save changes
        if user.save():
            return jsonify({
                'success': True,
                'message': 'Profile picture updated successfully',
                'profileUrl': data_uri,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to update profile picture'}), 500
        
    except Exception as e:
        print(f"Error updating profile picture: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Profile picture update error: {str(e)}'}), 500

@auth_bp.route('/reset-pin', methods=['POST'])
def reset_pin():
    """
    Verify user identity via wallet address and email for PIN reset
    
    This endpoint receives the user's wallet address and email,
    verifies they match an existing user, and initiates the PIN reset process
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Check if required fields are present
        if 'wallet_address' not in data or 'email' not in data:
            return jsonify({'success': False, 'message': 'Missing wallet_address or email'}), 400
        
        wallet_address = data['wallet_address']
        email = data['email']
        
        # Find user by wallet address and email using MongoDB
        user_doc = db.users.find_one({"wallet_address": wallet_address, "email": email})
        
        if not user_doc:
            # Don't reveal which field is incorrect for security
            return jsonify({
                'success': False, 
                'message': 'Unable to verify your identity. Please check your wallet and email.'
            }), 404
        
        # Convert document to User model
        from app.models.user import User
        user = User.from_dict(user_doc)
        
        # Generate reset token
        reset_token = auth_service.generate_reset_token()
        
        # Create timestamp for expiration
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=1)  # Token valid for 1 hour
        
        # Delete any existing reset tokens for this user using MongoDB
        db.pin_resets.delete_many({"user_id": user.id})
        
        # Create new reset token document
        reset_doc = {
            "user_id": user.id,
            "wallet_address": wallet_address,
            "reset_token": reset_token,
            "is_used": False,
            "expires_at": expires_at,
            "created_at": now
        }
        
        # Insert into MongoDB
        db.pin_resets.insert_one(reset_doc)
        
        # Log the activity using MongoDB
        activity = {
            "user_id": user.id,
            "activity_type": "pin_reset_request",
            "activity_description": "User requested PIN reset",
            "ip_address": request.remote_addr,
            "created_at": now
        }
        db.user_activities.insert_one(activity)
        
        # In a production environment, send an email to the user with the reset link
        # Here we'll just return a success message with the token for demonstration
        
        # For actual implementation, use an email service like this:
        # from app.services.email_service import EmailService
        # EmailService.send_pin_reset_email(user.email, reset_token)
        
        # System log entry using MongoDB
        log = {
            "log_type": "pin_reset_request",
            "log_message": f'PIN reset requested for user {user.id} ({user.email})',
            "created_at": now
        }
        db.system_logs.insert_one(log)
        
        # For development: return the token in the response
        # In production: return a message asking user to check their email
        return jsonify({
            'success': True,
            'message': 'Identity verified successfully. Check your email for instructions to reset your PIN.',
            'reset_token': reset_token,  # Remove this in production
            'user_id': user.id  # Remove this in production
        }), 200
        
    except Exception as e:
        print(f"Error in reset_pin: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'PIN reset error: {str(e)}'}), 500

@auth_bp.route('/set-new-pin', methods=['POST'])
def set_new_pin():
    """
    Set a new PIN using a valid reset token
    
    This endpoint verifies the reset token and allows the user to set a new PIN
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Check if required fields are present
        if 'reset_token' not in data or 'new_pin' not in data:
            return jsonify({'success': False, 'message': 'Missing reset_token or new_pin'}), 400
        
        reset_token = data['reset_token']
        new_pin = data['new_pin']
        
        # Validate PIN format (6 digits)
        if not new_pin.isdigit() or len(new_pin) != 6:
            return jsonify({'success': False, 'message': 'PIN must be 6 digits'}), 400
        
        # Find the reset token in the database using MongoDB
        now = datetime.utcnow()
        reset_doc = db.pin_resets.find_one({"reset_token": reset_token})
        
        if not reset_doc:
            return jsonify({'success': False, 'message': 'Invalid or expired reset token'}), 400
        
        # Check if token is expired
        if reset_doc.get("expires_at", now) < now:
            # Delete expired token
            db.pin_resets.delete_one({"reset_token": reset_token})
            return jsonify({'success': False, 'message': 'Reset token has expired'}), 400
            
        # Check if token has already been used
        if reset_doc.get("is_used", False):
            return jsonify({'success': False, 'message': 'This reset token has already been used'}), 400
            
        # Get user_id from reset document
        user_id = reset_doc.get("user_id")
        
        # Find the user using MongoDB
        user_doc = db.users.find_one({"_id": user_id})
        
        if not user_doc:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Convert document to User model
        from app.models.user import User
        user = User.from_dict(user_doc)
        
        # Set the new PIN
        user.set_pin(new_pin)
        
        # Update the user document with new PIN hash
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"security_pin": user.security_pin}}
        )
        
        # Mark token as used
        db.pin_resets.update_one(
            {"reset_token": reset_token},
            {"$set": {"is_used": True, "updated_at": now}}
        )
        
        # Log the activity using MongoDB
        activity = {
            "user_id": user.id,
            "activity_type": "pin_reset_complete",
            "activity_description": "User reset PIN successfully",
            "ip_address": request.remote_addr,
            "created_at": now
        }
        db.user_activities.insert_one(activity)
        
        # System log entry using MongoDB
        log = {
            "log_type": "pin_reset_complete",
            "log_message": f'PIN reset completed for user {user.id} ({user.email})',
            "created_at": now
        }
        db.system_logs.insert_one(log)
        
        # Generate JWT token to immediately log in the user
        token = auth_service.generate_token(user)
        
        return jsonify({
            'success': True,
            'message': 'PIN reset successfully',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Error in set_new_pin: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'PIN reset error: {str(e)}'}), 500