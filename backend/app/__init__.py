# app/__init__.py
from flask_jwt_extended import JWTManager
from flask import Flask, current_app, jsonify, make_response, request
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_pymongo import PyMongo
from app.config import Config
import pymongo
import uuid
import traceback

# Define your extensions here
mongo = PyMongo()
socketio = SocketIO()
jwt = JWTManager()

# MongoDB database reference - initialized during app creation
db = None

# Function to get the MongoDB database instance
def get_db():
    global db
    # Simply return the global db reference, avoiding any boolean checks on db object
    return db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Try to use direct MongoDB connection first with timeout parameters
    global db
    try:
        # Get MongoDB URI from config
        mongo_uri = app.config.get('MONGO_URI')
        if mongo_uri:
            # Create MongoDB client with shorter timeouts
            client = pymongo.MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Extract database name from URI or use default
            if '/' in mongo_uri:
                db_name = mongo_uri.split('/')[-1].split('?')[0]
            else:
                db_name = 'awardloop_app'
                
            # Connect to the database
            db = client[db_name]
            
            # Test connection with lightweight command
            db.command('ping')
            app.logger.info(f"MongoDB connected directly to {db_name}")
    except Exception as e:
        app.logger.error(f"Direct MongoDB connection failed: {str(e)}")
        app.logger.info("Falling back to PyMongo extension")
        
        # Fall back to Flask-PyMongo if direct connection fails
        mongo.init_app(app)
        db = mongo.db

    # Initialize other extensions
    socketio.init_app(app, cors_allowed_origins="*")
    jwt.init_app(app) 
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.wallet import wallet_bp
    from app.api.bidding import bidding_bp
    from app.api.referral import referral_bp
    from app.api.token import token_bp
    from app.api.webhook import webhook_bp
    from app.api.investment import investment_bp
    from app.api.admin import admin_bp
    from app.api.dashboard import dashboard_bp
    from app.api.test import test_bp
    from app.api.moralis import moralis_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(bidding_bp, url_prefix='/api/bidding')
    app.register_blueprint(referral_bp, url_prefix='/api/referral')
    app.register_blueprint(token_bp, url_prefix='/api/token')
    app.register_blueprint(webhook_bp, url_prefix='/api/webhook')
    app.register_blueprint(investment_bp, url_prefix='/api/investment')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(test_bp, url_prefix='/api/test')
    app.register_blueprint(moralis_bp)  # url_prefix already defined in blueprint
    
    # Add a direct webhook endpoint at the root level for Moralis verification
    @app.route('/webhook', methods=['POST', 'OPTIONS', 'GET'])
    def moralis_webhook_verification():
        """Direct webhook endpoint at root level that always returns success for Moralis verification"""
        # Handle OPTIONS request
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, x-signature')
            return response, 200
            
        try:
            # Log request details for debugging
            app.logger.info("Received request to root webhook endpoint")
            
            # Try to get JSON content for logging, but don't fail if there isn't any
            try:
                data = request.json
                app.logger.info(f"Webhook payload received: {str(data)[:200]}...")
            except Exception as e:
                app.logger.info(f"No JSON payload or could not parse: {str(e)}")
            
            # Always return success for verification
            return jsonify({
                "success": True
            }), 200
            
        except Exception as e:
            # Log the error but still return 200
            error_id = str(uuid.uuid4())[:8]
            app.logger.error(f"Error in webhook (ID: {error_id}): {str(e)}")
            
            # For webhook handlers, always return 200 even on errors
            # This prevents Moralis from retrying unnecessarily
            return jsonify({
                "success": True,
                "message": "Request processed with issues",
                "error_id": error_id
            }), 200
    
    # Initialize automated schedulers only if not in testing mode
    # This helps avoid circular imports during testing
    if not app.config.get('TESTING', False):
        with app.app_context():
            # Import schedulers only when needed (avoiding circular imports)
            from app.tasks.token_burn import init_scheduler as init_token_burn_scheduler
            init_token_burn_scheduler()
            
            # Only import the main scheduler if we're running the main app
            if app.config.get('INITIALIZE_SCHEDULERS', True):
                from app.tasks.scheduler import init_scheduler as init_main_scheduler
                init_main_scheduler()
    
    # Initialize Socket.IO handlers
    from app.socket_handlers import init_socket_handlers
    init_socket_handlers()
    
    return app