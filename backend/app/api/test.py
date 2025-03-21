"""
Test API endpoints for AwardLoop platform
Provides endpoints to trigger and monitor tests on the backend
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import sys
import logging
import threading
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_processes.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("awardloop-test-api")

test_bp = Blueprint('test', __name__)

def run_test_in_thread(test_func, app):
    """Run a test function in a separate thread with app context"""
    with app.app_context():
        try:
            test_func(app)
            logger.info(f"Test {test_func.__name__} completed successfully")
        except Exception as e:
            logger.error(f"Test {test_func.__name__} failed: {str(e)}")

@test_bp.route('/run-all', methods=['POST'])
@jwt_required()
def run_all_tests():
    """Run all tests on the backend"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, run_all_tests
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run all tests in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(run_all_tests, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'All tests started in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting tests: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/run-specific', methods=['POST'])
@jwt_required()
def run_specific_test():
    """Run a specific test on the backend"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get test name from request
        data = request.json
        test_name = data.get('test')
        
        if not test_name:
            return jsonify({'success': False, 'message': 'Test name is required'}), 400
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import (
            setup_test_environment, create_test_data, create_test_wallets,
            test_wallet_encryption, test_admin_fee_collection,
            test_referral_income_distribution, test_team_rewards_calculation,
            test_roi_distribution, test_transaction_processing,
            test_token_burning, test_bid_cycle_management,
            print_database_status
        )
        
        # Map test names to functions
        test_functions = {
            'data': create_test_data,
            'wallets': create_test_wallets,
            'encryption': test_wallet_encryption,
            'fees': test_admin_fee_collection,
            'referral': test_referral_income_distribution,
            'team': test_team_rewards_calculation,
            'roi': test_roi_distribution,
            'transactions': test_transaction_processing,
            'token': test_token_burning,
            'cycle': test_bid_cycle_management,
            'status': print_database_status
        }
        
        # Check if test name is valid
        if test_name not in test_functions:
            return jsonify({
                'success': False, 
                'message': f'Invalid test name. Valid tests are: {", ".join(test_functions.keys())}'
            }), 400
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run specific test in a background thread
        test_func = test_functions[test_name]
        thread = threading.Thread(target=run_test_in_thread, args=(test_func, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Test {test_name} started in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting test: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/status', methods=['GET'])
@jwt_required()
def get_test_status():
    """Get the status of test data in the database"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import function to print database status
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, print_database_status
        
        # Set up test environment
        app = setup_test_environment()
        
        # Get database status
        with app.app_context():
            from app import db
            from app.models.user import User
            from app.models.user_wallet import UserWallet
            from app.models.user_earnings import UserEarning
            from app.models.pending_transaction import PendingTransaction
            
            # Users
            users = User.query.filter(User.user_name.like('test_%')).all()
            user_list = [{'id': user.id, 'username': user.user_name} for user in users]
            
            # Wallets
            wallets = UserWallet.query.join(User).filter(User.user_name.like('test_%')).all()
            encrypted_count = sum(1 for w in wallets if w.encrypted_private_key is not None)
            
            # Earnings
            earnings = UserEarning.query.join(User).filter(User.user_name.like('test_%')).all()
            
            by_type = {}
            for earning in earnings:
                by_type[earning.earning_type] = by_type.get(earning.earning_type, 0) + 1
            
            # Pending Transactions
            pending_txs = PendingTransaction.query.all()
            
            by_status = {}
            for tx in pending_txs:
                # Get status field with fallback
                status = getattr(tx, 'status', getattr(tx, 'transaction_status', 'unknown'))
                by_status[status] = by_status.get(status, 0) + 1
        
        return jsonify({
            'success': True,
            'status': {
                'test_users': {
                    'count': len(users),
                    'users': user_list
                },
                'test_wallets': {
                    'count': len(wallets),
                    'encrypted': encrypted_count
                },
                'test_earnings': {
                    'count': len(earnings),
                    'by_type': by_type
                },
                'pending_transactions': {
                    'count': len(pending_txs),
                    'by_status': by_status
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting test status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_test_logs():
    """Get the latest test log entries"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get limit from query parameters
        limit = request.args.get('limit', 100, type=int)
        
        # Read log file
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'test_processes.log')
        
        if not os.path.exists(log_file):
            return jsonify({
                'success': True,
                'logs': [],
                'message': 'No log file found'
            }), 200
        
        # Read the last 'limit' lines from the log file
        try:
            with open(log_file, 'r') as f:
                # Read all lines and get the last 'limit' lines
                lines = f.readlines()
                last_lines = lines[-limit:] if len(lines) > limit else lines
                
            return jsonify({
                'success': True,
                'logs': last_lines,
                'count': len(last_lines)
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error reading log file: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error getting test logs: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Specific test endpoints

@test_bp.route('/create-data', methods=['POST'])
@jwt_required()
def create_data():
    """Create test data (users, referrals, investments)"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, create_test_data
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(create_test_data, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Creating test data in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/create-wallets', methods=['POST'])
@jwt_required()
def create_wallets():
    """Create test wallets for test users"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, create_test_wallets
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(create_test_wallets, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Creating test wallets in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating test wallets: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/wallet-encryption', methods=['POST'])
@jwt_required()
def wallet_encryption():
    """Test the wallet encryption process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_wallet_encryption
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_wallet_encryption, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing wallet encryption in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing wallet encryption: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/admin-fees', methods=['POST'])
@jwt_required()
def admin_fees():
    """Test the admin fee collection process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_admin_fee_collection
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_admin_fee_collection, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing admin fee collection in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing admin fee collection: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/referral-income', methods=['POST'])
@jwt_required()
def referral_income():
    """Test the referral income distribution process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_referral_income_distribution
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_referral_income_distribution, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing referral income distribution in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing referral income distribution: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/team-rewards', methods=['POST'])
@jwt_required()
def team_rewards():
    """Test the team rewards calculation process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_team_rewards_calculation
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_team_rewards_calculation, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing team rewards calculation in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing team rewards calculation: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/roi-distribution', methods=['POST'])
@jwt_required()
def roi_distribution():
    """Test the ROI distribution process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_roi_distribution
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_roi_distribution, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing ROI distribution in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing ROI distribution: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/transactions', methods=['POST'])
@jwt_required()
def transactions():
    """Test the transaction processing functionality"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_transaction_processing
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_transaction_processing, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing transaction processing in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing transaction processing: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/token-burning', methods=['POST'])
@jwt_required()
def token_burning():
    """Test the token burning process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_token_burning
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_token_burning, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing token burning in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing token burning: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@test_bp.route('/bid-cycle', methods=['POST'])
@jwt_required()
def bid_cycle():
    """Test the bid cycle management process"""
    try:
        # Check if user is admin
        current_user_id = get_jwt_identity()['id']
        
        from app.models.user import User
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Import test functions
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from test_all_processes import setup_test_environment, test_bid_cycle_management
        
        # Set up test environment
        app = setup_test_environment()
        
        # Run test in a background thread
        thread = threading.Thread(target=run_test_in_thread, args=(test_bid_cycle_management, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Testing bid cycle management in background',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
        
    except Exception as e:
        logger.error(f"Error testing bid cycle management: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500