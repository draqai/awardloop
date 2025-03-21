# app/models/transaction.py
from app import db
from datetime import datetime
from bson import ObjectId

class TatumTransaction:
    """
    Model for tracking Tatum blockchain transactions.
    Used for monitoring the status of cryptocurrency transfers.
    """
    COLLECTION = 'tatum_transactions'
    
    def __init__(self, transaction_id, transaction_type, amount,
                 user_id=None, blockchain_tx_id=None, status='pending',
                 reference_id=None, created_at=None, updated_at=None, id=None):
        """
        Initialize a new TatumTransaction instance
        
        Args:
            transaction_id (str): Reference ID for the transaction
            transaction_type (str): Type of transaction ('roi', 'referral', 'admin', etc.)
            amount (float): Transaction amount
            user_id (int or ObjectId, optional): User ID associated with this transaction. Defaults to None.
            blockchain_tx_id (str, optional): Actual blockchain transaction hash. Defaults to None.
            status (str, optional): Transaction status ('pending', 'processing', 'completed', 'failed'). Defaults to 'pending'.
            reference_id (str, optional): Optional reference to another entity. Defaults to None.
            created_at (datetime, optional): Creation timestamp. Defaults to current UTC time.
            updated_at (datetime, optional): Last update timestamp. Defaults to current UTC time.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.transaction_type = transaction_type
        self.amount = float(amount) if amount else 0.0
        self.blockchain_tx_id = blockchain_tx_id
        self.status = status
        self.reference_id = reference_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def __repr__(self):
        return f"<TatumTransaction {self.id} - {self.transaction_id} - {self.status}>"
    
    def to_dict(self):
        """
        Convert the TatumTransaction object to a dictionary
        
        Returns:
            dict: Dictionary representation of the TatumTransaction
        """
        return {
            "_id": self.id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "blockchain_tx_id": self.blockchain_tx_id,
            "status": self.status,
            "reference_id": self.reference_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def save(self):
        """
        Save the TatumTransaction object to the database
        
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
    def find_by_id(cls, transaction_id):
        """
        Find a TatumTransaction by ID
        
        Args:
            transaction_id (str or ObjectId): The ID of the TatumTransaction to find
            
        Returns:
            TatumTransaction or None: The found TatumTransaction object or None if not found
        """
        if isinstance(transaction_id, str):
            transaction_id = ObjectId(transaction_id)
            
        data = db[cls.COLLECTION].find_one({"_id": transaction_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_transaction_id(cls, transaction_id):
        """
        Find a transaction by Tatum transaction ID
        
        Args:
            transaction_id (str): The Tatum transaction ID
            
        Returns:
            TatumTransaction or None: The found TatumTransaction object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"transaction_id": transaction_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_blockchain_tx_id(cls, blockchain_tx_id):
        """
        Find a transaction by blockchain transaction hash
        
        Args:
            blockchain_tx_id (str): The blockchain transaction hash
            
        Returns:
            TatumTransaction or None: The found TatumTransaction object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"blockchain_tx_id": blockchain_tx_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_user_id(cls, user_id, limit=None, skip=None):
        """
        Find all transactions for a specific user
        
        Args:
            user_id (int or ObjectId): The ID of the user
            limit (int, optional): Maximum number of results to return. Defaults to None.
            skip (int, optional): Number of results to skip. Defaults to None.
            
        Returns:
            list: List of TatumTransaction objects for the user
        """
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                pass
                
        cursor = db[cls.COLLECTION].find({"user_id": user_id}).sort("created_at", -1)
        
        # Apply pagination if provided
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_status(cls, status):
        """
        Find all transactions with a specific status
        
        Args:
            status (str): The status to filter by
            
        Returns:
            list: List of TatumTransaction objects with the status
        """
        cursor = db[cls.COLLECTION].find({"status": status}).sort("created_at", 1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a TatumTransaction object from a dictionary
        
        Args:
            data (dict): Dictionary representing a TatumTransaction document
            
        Returns:
            TatumTransaction: A TatumTransaction object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            transaction_id=data.get("transaction_id"),
            user_id=data.get("user_id"),
            transaction_type=data.get("transaction_type"),
            amount=data.get("amount"),
            blockchain_tx_id=data.get("blockchain_tx_id"),
            status=data.get("status", "pending"),
            reference_id=data.get("reference_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )
    
    @classmethod
    def update_status(cls, transaction_id, status, blockchain_tx_id=None):
        """
        Update the status of a transaction
        
        Args:
            transaction_id (str or ObjectId): The ID of the transaction
            status (str): The new status
            blockchain_tx_id (str, optional): Blockchain transaction hash. Defaults to None.
            
        Returns:
            bool: True if updated, False otherwise
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if blockchain_tx_id:
            update_data["blockchain_tx_id"] = blockchain_tx_id
            
        result = db[cls.COLLECTION].update_one(
            {"transaction_id": transaction_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    @classmethod
    def delete_by_id(cls, transaction_id):
        """
        Delete a TatumTransaction by ID
        
        Args:
            transaction_id (str or ObjectId): ID of the TatumTransaction to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(transaction_id, str):
            try:
                transaction_id = ObjectId(transaction_id)
            except:
                # If not a valid ObjectId, try as transaction_id string
                result = db[cls.COLLECTION].delete_one({"transaction_id": transaction_id})
                return result.deleted_count > 0
            
        result = db[cls.COLLECTION].delete_one({"_id": transaction_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the TatumTransaction collection
        """
        db[cls.COLLECTION].create_index("transaction_id", unique=True)
        db[cls.COLLECTION].create_index("user_id")
        db[cls.COLLECTION].create_index("blockchain_tx_id", sparse=True)
        db[cls.COLLECTION].create_index("status")
        db[cls.COLLECTION].create_index("created_at")
        db[cls.COLLECTION].create_index([("user_id", 1), ("status", 1)])
        db[cls.COLLECTION].create_index([("transaction_type", 1), ("status", 1)])