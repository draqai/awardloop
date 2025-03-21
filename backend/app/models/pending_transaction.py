# app/models/pending_transaction.py
from app import db
from datetime import datetime
from bson import ObjectId
from decimal import Decimal

class PendingTransaction:
    """
    Model for tracking pending blockchain transactions that need to be executed.
    Used for direct peer-to-peer payments to external wallets.
    """
    COLLECTION = 'pending_transactions'
    
    def __init__(self, source_wallet_id, destination_address, amount, 
                 transaction_type, reference_id=None, status='pending',
                 created_at=None, processed_at=None, blockchain_tx_hash=None,
                 error_message=None, retry_count=0, id=None):
        """
        Initialize a new PendingTransaction instance
        
        Args:
            source_wallet_id (int or ObjectId): The ID of the source wallet
            destination_address (str): Destination blockchain address
            amount (float or Decimal): Transaction amount
            transaction_type (str): Type of transaction ('roi', 'referral', etc.)
            reference_id (str, optional): Reference ID (e.g., Investment ID). Defaults to None.
            status (str, optional): Transaction status ('pending', 'processing', 'completed', 'failed'). Defaults to 'pending'.
            created_at (datetime, optional): Creation timestamp. Defaults to current UTC time.
            processed_at (datetime, optional): When the transaction was processed. Defaults to None.
            blockchain_tx_hash (str, optional): Blockchain transaction hash. Defaults to None.
            error_message (str, optional): Error message if failed. Defaults to None.
            retry_count (int, optional): Number of retry attempts. Defaults to 0.
            id (ObjectId, optional): MongoDB ObjectId. Defaults to None.
        """
        self.id = id
        self.source_wallet_id = source_wallet_id
        
        # Handle amount as float or Decimal
        if isinstance(amount, (float, int, str)):
            self.amount = float(amount)
        else:
            self.amount = float(amount) if amount else 0.0
            
        self.destination_address = destination_address
        self.transaction_type = transaction_type
        self.reference_id = reference_id
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.processed_at = processed_at
        self.blockchain_tx_hash = blockchain_tx_hash
        self.error_message = error_message
        self.retry_count = retry_count
    
    def __repr__(self):
        dest = self.destination_address[:10] + "..." if self.destination_address else "None"
        return f"<PendingTransaction {self.id} - {self.amount} USDT to {dest}>"
    
    def to_dict(self):
        """
        Convert the PendingTransaction object to a dictionary
        
        Returns:
            dict: Dictionary representation of the PendingTransaction
        """
        return {
            "_id": self.id,
            "source_wallet_id": self.source_wallet_id,
            "destination_address": self.destination_address,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "reference_id": self.reference_id,
            "status": self.status,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "blockchain_tx_hash": self.blockchain_tx_hash,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }
    
    def save(self):
        """
        Save the PendingTransaction object to the database
        
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
        Find a PendingTransaction by ID
        
        Args:
            transaction_id (str or ObjectId): The ID of the PendingTransaction to find
            
        Returns:
            PendingTransaction or None: The found PendingTransaction object or None if not found
        """
        if isinstance(transaction_id, str):
            transaction_id = ObjectId(transaction_id)
            
        data = db[cls.COLLECTION].find_one({"_id": transaction_id})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def find_by_status(cls, status):
        """
        Find all transactions with a specific status
        
        Args:
            status (str): The status to filter by
            
        Returns:
            list: List of PendingTransaction objects with the status
        """
        cursor = db[cls.COLLECTION].find({"status": status}).sort("created_at", 1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_wallet_id(cls, wallet_id):
        """
        Find all transactions for a specific wallet
        
        Args:
            wallet_id (int or ObjectId): The ID of the wallet
            
        Returns:
            list: List of PendingTransaction objects for the wallet
        """
        if isinstance(wallet_id, str):
            try:
                wallet_id = ObjectId(wallet_id)
            except:
                pass
                
        cursor = db[cls.COLLECTION].find({"source_wallet_id": wallet_id}).sort("created_at", -1)
        return [cls._from_dict(data) for data in cursor]
    
    @classmethod
    def find_by_tx_hash(cls, tx_hash):
        """
        Find a transaction by blockchain transaction hash
        
        Args:
            tx_hash (str): The blockchain transaction hash
            
        Returns:
            PendingTransaction or None: The found PendingTransaction object or None if not found
        """
        data = db[cls.COLLECTION].find_one({"blockchain_tx_hash": tx_hash})
        
        if data:
            return cls._from_dict(data)
        return None
    
    @classmethod
    def _from_dict(cls, data):
        """
        Create a PendingTransaction object from a dictionary
        
        Args:
            data (dict): Dictionary representing a PendingTransaction document
            
        Returns:
            PendingTransaction: A PendingTransaction object created from the dictionary
        """
        return cls(
            id=data.get("_id"),
            source_wallet_id=data.get("source_wallet_id"),
            destination_address=data.get("destination_address"),
            amount=data.get("amount"),
            transaction_type=data.get("transaction_type"),
            reference_id=data.get("reference_id"),
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            processed_at=data.get("processed_at"),
            blockchain_tx_hash=data.get("blockchain_tx_hash"),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0)
        )
    
    @classmethod
    def update_status(cls, transaction_id, status, processed_at=None, 
                     blockchain_tx_hash=None, error_message=None):
        """
        Update the status of a transaction
        
        Args:
            transaction_id (str or ObjectId): The ID of the transaction
            status (str): The new status
            processed_at (datetime, optional): When the transaction was processed. Defaults to current UTC time.
            blockchain_tx_hash (str, optional): Blockchain transaction hash. Defaults to None.
            error_message (str, optional): Error message if failed. Defaults to None.
            
        Returns:
            bool: True if updated, False otherwise
        """
        if isinstance(transaction_id, str):
            transaction_id = ObjectId(transaction_id)
            
        update_data = {
            "status": status
        }
        
        if processed_at or status in ['completed', 'failed']:
            update_data["processed_at"] = processed_at or datetime.utcnow()
        
        if blockchain_tx_hash:
            update_data["blockchain_tx_hash"] = blockchain_tx_hash
            
        if error_message:
            update_data["error_message"] = error_message
            
        result = db[cls.COLLECTION].update_one(
            {"_id": transaction_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    @classmethod
    def increment_retry_count(cls, transaction_id):
        """
        Increment the retry count for a transaction
        
        Args:
            transaction_id (str or ObjectId): The ID of the transaction
            
        Returns:
            bool: True if updated, False otherwise
        """
        if isinstance(transaction_id, str):
            transaction_id = ObjectId(transaction_id)
            
        result = db[cls.COLLECTION].update_one(
            {"_id": transaction_id},
            {"$inc": {"retry_count": 1}}
        )
        
        return result.modified_count > 0
    
    @classmethod
    def delete_by_id(cls, transaction_id):
        """
        Delete a PendingTransaction by ID
        
        Args:
            transaction_id (str or ObjectId): ID of the PendingTransaction to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        if isinstance(transaction_id, str):
            transaction_id = ObjectId(transaction_id)
            
        result = db[cls.COLLECTION].delete_one({"_id": transaction_id})
        return result.deleted_count > 0
    
    @classmethod
    def ensure_indexes(cls):
        """
        Create indexes for the PendingTransaction collection
        """
        db[cls.COLLECTION].create_index("status")
        db[cls.COLLECTION].create_index("source_wallet_id")
        db[cls.COLLECTION].create_index("blockchain_tx_hash", sparse=True)
        db[cls.COLLECTION].create_index("created_at")
        db[cls.COLLECTION].create_index([("status", 1), ("created_at", 1)])