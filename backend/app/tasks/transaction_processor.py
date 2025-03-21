# app/tasks/transaction_processor.py
import logging
from datetime import datetime, timedelta
from app import create_app
from app.services.transaction_service import TransactionService
from app.services.tatum_hybrid_service import TatumHybridService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("transaction_processor.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Don't create a global app or db connection to avoid socket issues in threads
# Instead, create fresh connections within each function that needs them

def process_pending_transactions(batch_size=10, max_retries=3):
    """
    Process pending blockchain transactions for P2P payments.
    This executes the actual blockchain transfers for transactions created by the distribution system.
    
    Args:
        batch_size: Number of transactions to process in one batch
        max_retries: Maximum number of retry attempts for failed transactions
    """
    # Create a fresh app context for this thread/function
    app = create_app()
    
    # Use the app context to properly manage connections
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        logger.info("Starting transaction processor...")
        
        try:
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Initialize services
            tatum_service = TatumHybridService()
            transaction_service = TransactionService()
            
            # Get pending transactions using MongoDB
            pending_txs = list(db.pending_transactions.find(
                {"status": "pending"}
            ).sort(
                "created_at", 1  # Sort by created_at ascending
            ).limit(batch_size))
            
            if not pending_txs:
                logger.info("No pending transactions found")
                return {"success": True, "processed": 0, "message": "No pending transactions"}
            
            # Process each transaction
            processed_count = 0
            failed_count = 0
            total_amount = 0
            
            for pending_tx in pending_txs:
                try:
                    tx_id = pending_tx.get('_id')
                    
                    # Update status to processing using MongoDB
                    db.pending_transactions.update_one(
                        {"_id": tx_id},
                        {"$set": {"status": "processing"}}
                    )
                    
                    # Get source wallet ID and convert to ObjectId if needed
                    source_wallet_id = pending_tx.get('source_wallet_id')
                    if isinstance(source_wallet_id, str):
                        try:
                            source_wallet_id = ObjectId(source_wallet_id)
                        except:
                            pass
                    
                    # Get source wallet for the transaction using MongoDB
                    source_wallet = db.user_wallets.find_one({"_id": source_wallet_id})
                    
                    if not source_wallet:
                        logger.error(f"Source wallet {source_wallet_id} not found")
                        db.pending_transactions.update_one(
                            {"_id": tx_id},
                            {"$set": {
                                "status": "failed",
                                "error_message": "Source wallet not found"
                            }}
                        )
                        failed_count += 1
                        continue
                    
                    # Check if we have access to the private key
                    if not source_wallet.get('encrypted_private_key'):
                        logger.error(f"No private key available for wallet {source_wallet.get('_id')}")
                        db.pending_transactions.update_one(
                            {"_id": tx_id},
                            {"$set": {
                                "status": "failed",
                                "error_message": "No private key available"
                            }}
                        )
                        failed_count += 1
                        continue
                    
                    # Get admin ID for logging
                    from app.services.system_service import get_system_setting
                    admin_id = get_system_setting('admin_user_id', 1)
                    if isinstance(admin_id, str) and admin_id.isdigit():
                        admin_id = int(admin_id)
                    
                    # Get the decrypted private key (this is logged and secured)
                    from app.services.encryption_service import EncryptionService
                    encryption_service = EncryptionService()
                    private_key = encryption_service.decrypt_private_key(
                        source_wallet.get('encrypted_private_key'),
                        user_id=source_wallet.get('user_id'),
                        admin_id=admin_id,
                        reason="P2P payment execution"
                    )
                    
                    if not private_key:
                        logger.error(f"Failed to decrypt private key for wallet {source_wallet.get('_id')}")
                        db.pending_transactions.update_one(
                            {"_id": tx_id},
                            {"$set": {
                                "status": "failed",
                                "error_message": "Failed to decrypt private key",
                                "retry_count": pending_tx.get('retry_count', 0) + 1
                            }}
                        )
                        failed_count += 1
                        continue
                    
                    # Execute the blockchain transaction
                    tx_result = transaction_service.send_usdt(
                        from_address=source_wallet.get('wallet_address'),
                        to_address=pending_tx.get('destination_address'),
                        amount=pending_tx.get('amount'),
                        admin_private_key=private_key  # This is secure, using the right parameter
                    )
                    
                    if tx_result.get('success'):
                        # Mark as completed using MongoDB
                        db.pending_transactions.update_one(
                            {"_id": tx_id},
                            {"$set": {
                                "status": "completed",
                                "processed_at": datetime.utcnow(),
                                "blockchain_tx_hash": tx_result.get('txId')
                            }}
                        )
                        
                        # Update the TatumTransaction record using MongoDB
                        db.tatum_transactions.update_one(
                            {
                                "transaction_id": {"$regex": f"ROI-{pending_tx.get('reference_id')}-PART-.*"},
                                "status": "pending"
                            },
                            {"$set": {
                                "status": "completed",
                                "blockchain_tx_id": tx_result.get('txId')
                            }}
                        )
                        
                        processed_count += 1
                        total_amount += pending_tx.get('amount', 0)
                        
                        logger.info(f"Successfully processed P2P payment of {pending_tx.get('amount')} USDT to {pending_tx.get('destination_address')}")
                    else:
                        # Handle failure using MongoDB
                        error_msg = tx_result.get('message', 'Unknown error')
                        retry_count = pending_tx.get('retry_count', 0) + 1
                        
                        update_data = {
                            "retry_count": retry_count,
                            "error_message": error_msg
                        }
                        
                        if retry_count >= max_retries:
                            update_data["status"] = "failed"
                            logger.error(f"P2P payment failed after {max_retries} attempts: {error_msg}")
                        else:
                            update_data["status"] = "pending"  # Will be retried
                            logger.warning(f"P2P payment failed, will retry ({retry_count}/{max_retries}): {error_msg}")
                        
                        db.pending_transactions.update_one(
                            {"_id": tx_id},
                            {"$set": update_data}
                        )
                        
                        failed_count += 1
                    
                except Exception as e:
                    logger.exception(f"Error processing transaction {pending_tx.get('_id')}: {str(e)}")
                    
                    # Update status for retry using MongoDB
                    try:
                        retry_count = pending_tx.get('retry_count', 0) + 1
                        
                        update_data = {
                            "retry_count": retry_count
                        }
                        
                        if retry_count >= max_retries:
                            update_data["status"] = "failed"
                            update_data["error_message"] = str(e)[:255]  # Truncate if too long
                        else:
                            update_data["status"] = "pending"  # Will be retried
                        
                        db.pending_transactions.update_one(
                            {"_id": pending_tx.get('_id')},
                            {"$set": update_data}
                        )
                    except Exception as inner_e:
                        logger.exception(f"Error updating transaction status: {str(inner_e)}")
                    
                    failed_count += 1
                    continue
            
            logger.info(f"Transaction processing completed. Processed: {processed_count}, Failed: {failed_count}, Total: {total_amount}")
            return {
                "success": True,
                "processed": processed_count,
                "failed": failed_count,
                "total_amount": total_amount
            }
            
        except Exception as e:
            logger.exception(f"Error in transaction processor: {str(e)}")
            return {"success": False, "message": str(e)}

def cleanup_old_transactions():
    """
    Clean up old transactions that have been processed or failed.
    Moves them to an archive collection to keep the pending transactions collection small and efficient.
    """
    # Create a fresh app context for this thread/function
    app = create_app()
    
    # Use the app context to properly manage connections
    with app.app_context():
        # Get MongoDB database from the current app context
        from app import db
        try:
            # Import ObjectId for MongoDB ID handling
            from bson.objectid import ObjectId
            
            # Find completed transactions older than 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            old_txs = list(db.pending_transactions.find({
                "status": {"$in": ["completed", "failed"]},
                "processed_at": {"$lt": seven_days_ago}
            }))
            
            if not old_txs:
                return {"success": True, "message": "No old transactions to clean up"}
            
            # Create archive records and delete old records
            for tx in old_txs:
                # Create archive record with current timestamp
                archive_data = tx.copy()  # Copy all fields
                archive_data["original_id"] = str(tx.get("_id"))  # Convert ObjectId to string
                archive_data["archived_at"] = datetime.utcnow()
                
                # Remove _id to allow MongoDB to create a new one
                if "_id" in archive_data:
                    del archive_data["_id"]
                
                # Insert into archive collection
                db.transaction_archive.insert_one(archive_data)
                
                # Delete the original
                db.pending_transactions.delete_one({"_id": tx.get("_id")})
            
            logger.info(f"Cleaned up {len(old_txs)} old transactions")
            return {"success": True, "cleaned": len(old_txs)}
            
        except Exception as e:
            logger.exception(f"Error in transaction cleanup: {str(e)}")
            return {"success": False, "message": str(e)}

def run_processor():
    """Run the transaction processor and cleanup"""
    # Create a new app context for these operations
    app = create_app()
    with app.app_context():
        process_pending_transactions()
        cleanup_old_transactions()

if __name__ == "__main__":
    # This allows the script to be run directly
    # Create a fresh app context when running directly
    app = create_app()
    with app.app_context():
        run_processor()