# app/services/encryption_service.py
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
from app import db
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    Service for securely encrypting and decrypting sensitive wallet information.
    Uses Fernet symmetric encryption (AES-128-CBC with PKCS7 padding).
    """
    
    def __init__(self, master_key=None):
        """
        Initialize the encryption service with a master key.
        
        Args:
            master_key: Optional master key. If not provided, will attempt to load from environment.
        """
        # Get master key from parameter, environment, or generate a new one
        self.master_key = master_key or os.environ.get('ENCRYPTION_MASTER_KEY')
        
        # If no master key is provided or found in environment, log warning
        if not self.master_key:
            logger.warning("No encryption master key provided. Using fallback method.")
            # In production, you should not generate keys this way
            # This is just a fallback for development
            salt = b'awardloop_salt_value'  # In production, use a secure random salt
            app_secret = os.environ.get('SECRET_KEY', 'fallback_dev_only')
            
            # Derive a key from the app secret (not ideal for production)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(app_secret.encode()))
            self.master_key = key
            
        # Initialize Fernet with the master key
        try:
            self.fernet = Fernet(self.master_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def encrypt_private_key(self, private_key, user_id=None):
        """
        Encrypt a private key before storing in database.
        
        Args:
            private_key: Private key to encrypt
            user_id: Optional user ID for logging
            
        Returns:
            Encrypted key as a string
        """
        if not private_key:
            return None
        
        try:
            # Convert to bytes if string
            if isinstance(private_key, str):
                private_key = private_key.encode()
                
            # Encrypt the key
            encrypted_key = self.fernet.encrypt(private_key)
            
            # Log the encryption (without the actual key)
            if user_id:
                logger.info(f"Encrypted private key for user {user_id}")
            
            # Return base64 encoded string for storage
            return base64.urlsafe_b64encode(encrypted_key).decode()
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            if user_id:
                logger.error(f"Failed to encrypt key for user {user_id}")
            return None
    
    def decrypt_private_key(self, encrypted_key, user_id=None, admin_id=None, reason=None):
        """
        Decrypt a private key from database.
        
        Args:
            encrypted_key: Encrypted key to decrypt
            user_id: User ID the key belongs to
            admin_id: Admin ID requesting decryption (for auditing)
            reason: Reason for decryption (for auditing)
            
        Returns:
            Decrypted private key as a string
        """
        if not encrypted_key:
            return None
            
        try:
            # Record access attempt in database
            if user_id and admin_id and reason:
                self._log_key_access(user_id, admin_id, reason)
            
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key)
            
            # Decrypt
            decrypted_key = self.fernet.decrypt(encrypted_bytes)
            
            # Return as string
            return decrypted_key.decode()
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            if user_id:
                logger.error(f"Failed to decrypt key for user {user_id}")
            return None
    
    def rotate_encryption_key(self, new_master_key):
        """
        Rotate encryption key by re-encrypting all private keys with a new master key.
        
        Args:
            new_master_key: New master key to use
            
        Returns:
            Number of records updated
        """
        try:
            # Create a new cipher with the new key
            new_fernet = Fernet(new_master_key)
            
            # Get all wallet records with encrypted keys
            wallets = list(db.user_wallets.find({"encrypted_private_key": {"$ne": None}}))
            
            # Track rotation in database
            rotation_data = {
                "key_identifier": f"key_rotation_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                "rotated_by": "system",
                "affected_records": len(wallets),
                "status": "in_progress",
                "created_at": datetime.utcnow()
            }
            rotation_result = db.encryption_key_rotation.insert_one(rotation_data)
            rotation_id = rotation_result.inserted_id
            
            updated_count = 0
            
            # Re-encrypt each key with the new master key
            for wallet in wallets:
                try:
                    # Decrypt with old key
                    decrypted_key = self.decrypt_private_key(wallet.get('encrypted_private_key'))
                    if decrypted_key:
                        # Re-encrypt with new key
                        encrypted_key = base64.urlsafe_b64encode(
                            new_fernet.encrypt(decrypted_key.encode())
                        ).decode()
                        
                        # Update wallet record
                        db.user_wallets.update_one(
                            {"_id": wallet.get('_id')},
                            {
                                "$set": {
                                    "encrypted_private_key": encrypted_key,
                                    "encryption_version": 'v2',
                                    "key_encrypted_at": datetime.utcnow()
                                }
                            }
                        )
                        updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to rotate key for wallet {wallet.get('_id')}: {e}")
            
            # Update the master key reference
            self.master_key = new_master_key
            self.fernet = new_fernet
            
            # Update system settings
            db.system_settings.update_one(
                {"setting_key": "encryption_key_id"},
                {"$set": {
                    "setting_value": f"master_key_v{rotation_id}",
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )
            
            # Update rotation record
            db.encryption_key_rotation.update_one(
                {"_id": rotation_id},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "affected_records": updated_count
                }}
            )
            
            logger.info(f"Key rotation completed. Updated {updated_count} records.")
            return updated_count
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            
            # Update rotation record to failed if it exists
            if rotation_id:
                try:
                    db.encryption_key_rotation.update_one(
                        {"_id": rotation_id},
                        {"$set": {
                            "status": "failed",
                            "completed_at": datetime.utcnow()
                        }}
                    )
                except Exception as update_error:
                    logger.error(f"Failed to update rotation status: {update_error}")
                
            raise
    
    def _log_key_access(self, wallet_id, user_id, reason, ip_address=None):
        """
        Log access to a private key for auditing purposes.
        
        Args:
            wallet_id: ID of the wallet being accessed
            user_id: ID of the user requesting access
            reason: Reason for accessing the key
            ip_address: Optional IP address of the requester
        """
        try:
            # Convert IDs to ObjectId if they are strings
            if isinstance(wallet_id, str) and ObjectId.is_valid(wallet_id):
                wallet_id = ObjectId(wallet_id)
            if isinstance(user_id, str) and ObjectId.is_valid(user_id):
                user_id = ObjectId(user_id)
                
            # Create log entry document
            log_entry = {
                "user_wallet_id": wallet_id,
                "accessed_by": user_id,
                "access_reason": reason,
                "ip_address": ip_address,
                "was_successful": True,
                "access_time": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            # Insert into MongoDB
            db.wallet_key_access_log.insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log key access: {e}")
            # Don't raise exception to avoid blocking the main decryption operation