#!/usr/bin/env python
import argparse
import eventlet # type: ignore
eventlet.monkey_patch()  # This line should be right after importing eventlet
from app import create_app, socketio, mongo
from app.db_init import init_mongodb, create_admin_user_if_not_exists
from flask import request

eventlet.monkey_patch()

# Parse command line arguments
parser = argparse.ArgumentParser(description='AwardLoop Backend Server')
parser.add_argument('--migrate', action='store_true', help='Migrate data from MySQL to MongoDB')
parser.add_argument('--init-db', action='store_true', help='Initialize MongoDB with indexes and default data')
args = parser.parse_args()

# Create the Flask app
app = create_app()

# Add CORS preflight handler after app is created
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        print(f"Handling OPTIONS request for path: {request.path}")
    return None

# Use Flask app context for database operations
with app.app_context():
    # Always ensure MongoDB is initialized with proper indexes
    init_mongodb()
    create_admin_user_if_not_exists()
    
    # Run data migration if requested
    if args.migrate:
        try:
            from app.db_migration import migrate_from_mysql_to_mongodb
            print("Starting data migration from MySQL to MongoDB...")
            success = migrate_from_mysql_to_mongodb()
            if success:
                print("Data migration completed successfully!")
            else:
                print("Data migration completed with errors. Check logs for details.")
        except ImportError:
            print("Migration module not found. Skipping migration.")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            print("Migration failed. See error details above.")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)