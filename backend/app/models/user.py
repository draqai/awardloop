# app/models/user.py
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId

class User:
    # Collection name
    collection = 'users'
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find a user by their ID"""
        if isinstance(user_id, str):
            # Convert string ID to ObjectId if needed
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        user_data = db[cls.collection].find_one({'_id': user_id})
        return cls(user_data) if user_data else None
    
    @classmethod
    def find_by_sponsor_id(cls, sponsor_id):
        """Find a user by their sponsor ID"""
        user_data = db[cls.collection].find_one({'sponsor_id': sponsor_id})
        return cls(user_data) if user_data else None
    
    @classmethod
    def find_by_email(cls, email):
        """Find a user by their email"""
        user_data = db[cls.collection].find_one({'email': email})
        return cls(user_data) if user_data else None
    
    @classmethod
    def find_by_wallet_address(cls, wallet_address):
        """Find a user by their wallet address with multiple lookup strategies"""
        if not wallet_address:
            print("WARNING: Empty wallet address provided to find_by_wallet_address")
            return None
            
        # First try exact match
        user_data = db[cls.collection].find_one({'wallet_address': wallet_address})
        if user_data:
            print(f"Found user with exact wallet address match: {wallet_address}")
            return cls(user_data)
            
        # If not found, try case-insensitive and format variations
        print(f"No exact match for wallet address: {wallet_address}, trying alternatives")
        
        # Try with whitespace trimmed
        if wallet_address != wallet_address.strip():
            trimmed = wallet_address.strip()
            print(f"Trying with trimmed whitespace: '{trimmed}'")
            user_data = db[cls.collection].find_one({'wallet_address': trimmed})
            if user_data:
                print(f"Found user with trimmed wallet address: {trimmed}")
                return cls(user_data)
                
        try:
            # Try case-insensitive match with regex
            import re
            normalized = wallet_address.strip()
            try:
                regex = re.compile(f"^{re.escape(normalized)}$", re.IGNORECASE)
                user_data = db[cls.collection].find_one({'wallet_address': {'$regex': regex}})
                if user_data:
                    print(f"Found user with case-insensitive wallet address: {user_data.get('wallet_address')}")
                    return cls(user_data)
            except Exception as regex_error:
                print(f"Error in regex lookup: {str(regex_error)}")
                
            # Try with and without 0x prefix
            if normalized.startswith('0x'):
                without_prefix = normalized[2:]
                print(f"Trying without 0x prefix: '{without_prefix}'")
                user_data = db[cls.collection].find_one({'wallet_address': without_prefix})
                if user_data:
                    print(f"Found user with non-prefixed wallet address: {without_prefix}")
                    return cls(user_data)
            else:
                with_prefix = f"0x{normalized}"
                print(f"Trying with 0x prefix: '{with_prefix}'")
                user_data = db[cls.collection].find_one({'wallet_address': with_prefix})
                if user_data:
                    print(f"Found user with prefixed wallet address: {with_prefix}")
                    return cls(user_data)
                    
        except Exception as e:
            print(f"Error during wallet address lookup: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
        print(f"No user found for wallet address: '{wallet_address}' after trying all lookup strategies")
        return None
    
    def __init__(self, data=None):
        # Default values
        self._id = None
        self.sponsor_id = None
        self.user_name = None
        self.email = None
        self.wallet_address = None
        self.security_pin = None
        self.balance = 0.00
        self.is_admin = False
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Initialize social media fields with empty values
        self.facebook_profile = ""
        self.twitter_profile = ""
        self.instagram_profile = ""
        self.profile_image = None
        
        # Apply data if provided
        if data:
            for key, value in data.items():
                # Skip 'id' since it's a read-only property
                if key == 'id' or key == '_id':
                    # Special handling for ID fields
                    if key == 'id':
                        self._id = value
                    else:  # key == '_id'
                        self._id = value
                    continue
                    
                try:
                    setattr(self, key, value)
                except AttributeError as e:
                    print(f"Warning in __init__: Could not set attribute '{key}': {str(e)}")
    
    @classmethod
    def from_dict(cls, data):
        """Convert a MongoDB document to a User object"""
        if not data:
            return None
        
        # Create a new User object
        user = cls()
        
        # Special handling for _id field
        if '_id' in data:
            user._id = data['_id']
        
        # Map MongoDB document fields to User object attributes
        for key, value in data.items():
            if key == '_id' or key == 'id':
                # Skip id fields as they're handled specially
                continue
                
            try:
                setattr(user, key, value)
            except AttributeError as e:
                print(f"Warning: Could not set attribute '{key}': {str(e)}")
                # Store in __dict__ as fallback
                user.__dict__[key] = value
        
        print(f"Created User object from document: id={user.id}, sponsor_id={user.sponsor_id}")
        return user
        
    @property
    def id(self):
        """Property to maintain backward compatibility with SQLAlchemy model"""
        return self._id
    
    def set_pin(self, pin):
        self.security_pin = generate_password_hash(pin, method='pbkdf2:sha256')
    
    def check_pin(self, pin):
        try:
            # More secure logging - mask PIN and don't show actual hash
            masked_pin = f"{pin[:1]}{'*' * (len(pin) - 2)}{pin[-1:]}" if len(pin) > 2 else "****"
            print(f"Checking PIN for user {self.id} ({self.sponsor_id})")
            print(f"Security PIN hash exists: {bool(self.security_pin)}")
            print(f"Testing with masked pin: {masked_pin}")
            
            # Check for None or empty string first
            if not self.security_pin:
                print("Security PIN is None or empty!")
                if pin == '123456':  # Default PIN for testing
                    print("Using default admin PIN - setting new hash")
                    self.set_pin(pin)
                    save_result = self.save()
                    print(f"PIN hash saved successfully: {save_result}")
                    return True
                return False

            try:
                # Try to check with the existing hash
                result = check_password_hash(self.security_pin, pin)
                print(f"PIN check result: {result}")
                return result
            except Exception as hash_error:
                # More detailed error handling for hash format issues
                error_msg = str(hash_error)
                print(f"PIN check error: {error_msg}")
                
                # Handle specific hash format errors
                if 'unsupported hash type scrypt' in error_msg.lower() or 'malformed' in error_msg.lower():
                    # Assume the PIN is correct for this login and update it to the new format
                    # This provides a migration path for existing users
                    print(f"Migrating user {self.id} from old hash format to pbkdf2")
                    self.set_pin(pin)
                    save_result = self.save()
                    print(f"Migration result - hash saved: {save_result}")
                    return True
                    
                # For any other hash error, log details but fail verification
                print(f"Hash verification failed: {error_msg}")
                return False
        
        except Exception as e:
            # Catch-all for any other unexpected errors
            print(f"Unexpected error in PIN verification: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def save(self):
        """Save user to the database"""
        data = self.to_mongo()
        
        # Update timestamp
        data['updated_at'] = datetime.utcnow()
        
        if self._id:
            # Update existing user
            # Debug log the ID type
            print(f"DEBUG - Saving user with _id: {self._id} (type: {type(self._id)})")
            
            # First perform a direct query to verify the document exists and ID type
            direct_query = None
            direct_result = None
            
            # Try different ways to find the document
            if isinstance(self._id, int):
                # For integer IDs, try direct integer lookup
                direct_query = {'_id': self._id}
                direct_result = db[self.collection].find_one(direct_query)
                print(f"DEBUG - Direct lookup with integer ID {self._id}: {direct_result is not None}")
                
                # If not found, try other fields as fallback
                if not direct_result and self.sponsor_id:
                    alt_query = {'sponsor_id': self.sponsor_id}
                    direct_result = db[self.collection].find_one(alt_query)
                    if direct_result:
                        direct_query = alt_query
                        print(f"DEBUG - Found by sponsor_id: {self.sponsor_id}")
            elif isinstance(self._id, str):
                # Try ObjectId conversion
                try:
                    obj_id = ObjectId(self._id)
                    direct_query = {'_id': obj_id}
                    direct_result = db[self.collection].find_one(direct_query)
                    print(f"DEBUG - Direct lookup with ObjectId: {direct_result is not None}")
                except:
                    # If not a valid ObjectId, try string ID directly
                    direct_query = {'_id': self._id}
                    direct_result = db[self.collection].find_one(direct_query)
                    print(f"DEBUG - Direct lookup with string ID: {direct_result is not None}")
                
                # If not found and we have sponsor_id, try that as fallback
                if not direct_result and self.sponsor_id:
                    alt_query = {'sponsor_id': self.sponsor_id}
                    direct_result = db[self.collection].find_one(alt_query)
                    if direct_result:
                        direct_query = alt_query
                        print(f"DEBUG - Found by sponsor_id: {self.sponsor_id}")
            else:
                # For any other type, try direct
                direct_query = {'_id': self._id}
                direct_result = db[self.collection].find_one(direct_query)
                print(f"DEBUG - Direct lookup with ID type {type(self._id)}: {direct_result is not None}")
            
            # If document wasn't found by any method, this is an error
            if not direct_result:
                print(f"DEBUG - Critical error: Document not found with any ID method")
                # Last ditch effort - try using sponsor_id if available
                if self.sponsor_id:
                    print(f"DEBUG - Trying to save using sponsor_id instead of _id")
                    # Ensure _id is not in data to avoid conflicts
                    if '_id' in data:
                        del data['_id']
                    try:
                        result = db[self.collection].update_one(
                            {'sponsor_id': self.sponsor_id},
                            {'$set': data}
                        )
                        success = result.matched_count > 0
                        print(f"DEBUG - Sponsor_id update result: {success}")
                        return success
                    except Exception as e:
                        print(f"DEBUG - Sponsor_id update error: {str(e)}")
                return False
            
            # Use the successful direct query for the update
            query = direct_query
            print(f"DEBUG - Using verified query: {query}")
            
            # Ensure _id is removed from update data
            if '_id' in data:
                del data['_id']
                print("DEBUG - Removed _id from update data")
                
            # Log update operation
            print(f"DEBUG - Update query: {query}")
            print(f"DEBUG - Update data: {data}")
            
            # Perform update
            try:
                result = db[self.collection].update_one(
                    query,
                    {'$set': data}
                )
                print(f"DEBUG - Update result: {result.matched_count} matched, {result.modified_count} modified")
                return result.matched_count > 0  # Success if document was found, even if no change needed
            except Exception as e:
                print(f"DEBUG - Update error: {str(e)}")
                return False
        else:
            # Create new user with timestamp
            data['created_at'] = datetime.utcnow()
            try:
                result = db[self.collection].insert_one(data)
                self._id = result.inserted_id
                return True
            except DuplicateKeyError:
                return False
    
    def to_mongo(self):
        """Convert user object to MongoDB document format"""
        data = {
            'sponsor_id': self.sponsor_id,
            'user_name': self.user_name,
            'email': self.email,
            'wallet_address': self.wallet_address,
            'security_pin': self.security_pin,
            'balance': float(self.balance),
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'updated_at': self.updated_at,
            # Always include social media fields
            'facebook_profile': getattr(self, 'facebook_profile', ''),
            'twitter_profile': getattr(self, 'twitter_profile', ''),
            'instagram_profile': getattr(self, 'instagram_profile', '')
        }
        
        # Include profile image only if it exists (can be None)
        if hasattr(self, 'profile_image') and self.profile_image is not None:
            data['profile_image'] = self.profile_image
        
        # Only include _id if it exists
        if self._id:
            data['_id'] = self._id
            
        # Print debug info
        print(f"DEBUG - to_mongo data: {data}")
            
        return data
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        data = {
            'id': str(self._id),
            'sponsor_id': self.sponsor_id,
            'user_name': self.user_name,
            'email': self.email,
            'wallet_address': self.wallet_address,
            'balance': float(self.balance),
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.created_at, datetime) else str(self.created_at)
        }
        
        # Include social media fields if they exist
        for field in ['facebook_profile', 'twitter_profile', 'instagram_profile', 'profile_image']:
            if hasattr(self, field) and getattr(self, field) is not None:
                data[field] = getattr(self, field)
                
        return data
    
    def __repr__(self):
        return f"<User {self.user_name} ({self.sponsor_id})>"
    
    @classmethod
    def ensure_indexes(cls):
        """Create indexes for the users collection"""
        db[cls.collection].create_index('sponsor_id', unique=True)
        db[cls.collection].create_index('email', unique=True)
        db[cls.collection].create_index('wallet_address', unique=True)