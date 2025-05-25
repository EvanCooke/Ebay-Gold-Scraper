import hashlib
from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv
from flask import send_from_directory, current_app

load_dotenv()

# I dont know what blueprints do or why we separate them
notifications_bp = Blueprint('notifications', __name__)
frontend_bp = Blueprint('frontend', __name__)

# eBay API credentials and endpoint
# These should be stored securely and not hardcoded in production
# https://developer.ebay.com/marketplace-account-deletion
VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
ENDPOINT_URL = os.getenv('ENDPOINT_URL')

# Define allowed file extensions for security
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot'}

@notifications_bp.route('/ebay/notifications', methods=['GET', 'POST'])
def ebay_notifications():
    if request.method == 'GET':
        # Handle challenge from eBay
        challenge_code = request.args.get('challenge_code')
        
        if challenge_code:
            to_hash = challenge_code + VERIFICATION_TOKEN + ENDPOINT_URL
            hashed = hashlib.sha256(to_hash.encode('utf-8')).hexdigest()
            
            response = {
                "challengeResponse": hashed
            }
            return jsonify(response), 200
        
        #return jsonify({"error": "No challenge_code provided"}), 400

    elif request.method == 'POST':
        # Handle actual notifications
        try:
            data = request.get_json()
            print("Received eBay Notification:", data)
            return jsonify({"message": "Notification received successfully"}), 200
        except Exception as e:
            print("Error processing notification:", str(e))
            return jsonify({"error": "Failed to process notification"}), 500
        

@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def serve_react_app(path):
    static_folder = current_app.static_folder
    
    # If someone asks for a specific file, check if it's allowed
    if path:
        # Get file extension
        _, ext = os.path.splitext(path.lower())
        
        # Check if extension is allowed
        if ext not in ALLOWED_EXTENSIONS:
            return send_from_directory(static_folder, 'index.html')
            
        # Check if file exists and serve it
        if os.path.exists(os.path.join(static_folder, path)):
            return send_from_directory(static_folder, path)
    
    # Default: serve the React app
    return send_from_directory(static_folder, 'index.html')