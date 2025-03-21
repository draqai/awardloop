# app/tasks/blockchain_scanner.py
"""
IMPORTANT: This module has been intentionally disabled.

The system now relies solely on Tatum webhooks for transaction detection,
as requested. No periodic blockchain scanning or fallback mechanisms are used.

See FINAL_TRANSACTION_SYSTEM_README.md for details on the webhook-based approach.
"""

def scan_for_missed_transactions(hours_back=24):
    """
    This function has been disabled.
    The system now relies solely on Tatum webhooks for transaction detection.
    """
    print("Blockchain scanner has been disabled. Using Tatum webhooks only.")
    return {
        "success": False,
        "error": "Blockchain scanner has been disabled. Using Tatum webhooks only."
    }

def run_scanner():
    """This function has been disabled."""
    print("Blockchain scanner has been disabled. Using Tatum webhooks only.")
    return {
        "success": False,
        "error": "Blockchain scanner has been disabled. Using Tatum webhooks only."
    }