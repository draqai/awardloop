# app/models/user_wallet.py
from app import db
from datetime import datetime
from bson import ObjectId

class UserWallet:
    """
    UserWallet model for MongoDB
    
    Represents a user's cryptocurrency wallet with encrypted private key
    """
    
    COLLECTION = 'user_wallets'
    
    def __init__(self, user_id, wallet_type='user', kms_id=None,
                 deposit_address=None, xpub=None, encrypted_private_key=None,
                 encryption_version='v1', key_encrypted_at=None,
                 last_encryption_check=None, blockchain='BSC',
                 created_at=None, updated_at=None, id=None):
        """
        Initialize a new UserWallet instance
        
        Args:
            user_id (int or ObjectId): The ID of the wallet owner
            wallet_type (str, optional): Type of wallet ('system' or 'user'). Defaults to 'user'.
            kms_id (str, optional): KMS identifier. Defaults to None.
            deposit_address (str, optional): Blockchain deposit address. Defaults to None.
            xpub (str, optional): Extended public key. Defaults to None.
            encrypted_private_key (str, optional): Encrypted private key (never store unencrypted). Defaults to None.
            encryption_version (str, optional): Version of encryption used. Defaults to 'v1'.
            key_encrypted_at (datetime, optional): When the private key was encrypted. Defaults to None.
            last_encryption_check (datetime, optional): Last time encryption was verified. Defaults to None.
            blockchain (str, optional): Blockchain network. Defaults to 'BSC'.
            created_at (datetime, optional): Creation timestamp. Defaults to current UTC time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current UTC time.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.user_id = user_id
        self.wallet_type = wallet_type
        self.kms_id = kms_id
        self.deposit_address = deposit_address
        self.xpub = xpub
        self.encrypted_private_key = encrypted_private_key
        self.encryption_version = encryption_version
        self.key_encrypted_at = key_encrypted_at
        self.last_encryption_check = last_encryption_check
        self.blockchain = blockchain
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def __repr__(self):
        return f"<UserWallet {self.wallet_type} - {self.deposit_address}>"
    
    @property
    def has_encrypted_key(self):
        """Check if this wallet has an encrypted private key"""
        return self.encrypted_private_key is not None
    
    def to_dict(self):
        """
        Convert the UserWallet object to a dictionary
        
        Returns:
            dict: Dictionary representation of the UserWallet
        """
        return {
            "_id": self.id,
            "user_id": self.user_id,
            "wallet_type": self.wallet_type,
            "kms_id": self.kms_id,
            "deposit_address": self.deposit_address,
            "xpub": self.xpub,
            "encrypted_private_key": self.encrypted_private_key,
            "encryption_version": self.encryption_version,
            "key_encrypted_at": self.key_encrypted_at,
            "last_encryption_check": self.last_encryption_check,
            "blockchain": self.blockchain,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def save(self):
        """
        Save the UserWallet object to the database
        
        Returns:
            ObjectId: The ID of the inserted or updated document
        """
        data = self.to_dict()
        
        if self.id:
            # Update existing document
            data.pop("_id", None)  # Remove _id for update operation
            result = db[self.COLLECTION].update_one(
                {"_id": self.id},
                {"$set": data}
            )
            return self.id
        else:
            # Insert new document
            data.pop("_id", None)  # Remove None _id for insert
            result = db[self.COLLECTION].insert_one(data)
            self.id = result.inserted_id
            return self.id
    
    @classmethod
    def find_by_id(cls, wallet_id):
        """
        Find a UserWallet by ID
        
        Args:
            wallet_id (str or ObjectId): The ID of the UserWallet to find
            
        Returns:
            UserWallet or None: The found UserWallet object or None if not found
        """
        if isinstance(wallet_id, str):
            wallet_id = ObjectId(wallet_id)
            
        data = db[cls.COLLECTION].find_one({"_id": wallet_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """
        Find all wallets for a specific user
        
        Args:
            user_id (int or ObjectId): The ID of the user
            
        Returns:
            list: List of UserWallet objects for the user
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        cursor = db[cls.COLLECTION].find({"user_id": user_id})
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_deposit_address(cls, deposit_address):
        """
        Find a wallet by deposit address
        
        Args:
            deposit_address (str): The blockchain deposit address
            
        Returns:
            UserWallet or None: The found UserWallet object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"deposit_address": deposit_address})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_system_wallets(cls):
        """
        Find all system wallets
        
        Returns:
            list: List of system UserWallet objects
        """
        cursor = db[cls.COLLECTION].find({"wallet_type": "system"})
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a UserWallet object from a dictionary
        
        Args:
            data (dict): Dictionary representing a UserWallet document
            
        Returns:
            UserWallet: A UserWallet object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            user_id=data.get("user_id"),
            wallet_type=data.get("wallet_type", "user"),
            kms_id=data.get("kms_id"),
            deposit_address=data.get("deposit_address"),
            xpub=data.get("xpub"),
            encrypted_private_key=data.get("encrypted_private_key"),
            encryption_version=data.get("encryption_version", "v1"),
            key_encrypted_at=data.get("key_encrypted_at"),
            last_encryption_check=data.get("last_encryption_check"),
            blockchain=data.get("blockchain", "BSC"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    @classmethod
    def get_user(cls, wallet_id):
        """
        Get the user associated with this wallet
        
        Args:
            wallet_id (str or ObjectId): ID of the UserWallet
            
        Returns:
            User or None: The associated User object or None
        """
        from app.models.user import User
        
        wallet = cls.find_by_id(wallet_id)
        if not wallet:
            return None
            
        return User.find_by_id(wallet.user_id)
    
    @classmethod
    def get_access_logs(cls, wallet_id):
        """
        Get access logs for this wallet
        
        Args:
            wallet_id (str or ObjectId): ID of the UserWallet
            
        Returns:
            list: List of wallet access log documents
        """
        if isinstance(wallet_id, str):
            wallet_id = ObjectId(wallet_id)
            
        # Query access logs from separate collection
        cursor = db.wallet_key_access_logs.find({"wallet_id": wallet_id}).sort("accessed_at", -1)
        return list(cursor)
    
    @classmethod
    def delete_by_id(cls, wallet_id):
        """
        Delete a UserWallet by ID
        
        Args:
            wallet_id (str or ObjectId): ID of the UserWallet to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(wallet_id, str):
            wallet_id = ObjectId(wallet_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": wallet_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the UserWallet collection
        """
        db[cls.COLLECTION].create_index("user_id")
        db[cls.COLLECTION].create_index("deposit_address", unique=True, sparse=True)
        db[cls.COLLECTION].create_index("wallet_type")
        db[cls.COLLECTION].create_index("blockchain")
        db[cls.COLLECTION].create_index([("user_id", 1), ("wallet_type", 1)])