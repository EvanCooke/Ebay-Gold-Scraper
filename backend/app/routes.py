import hashlib
from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

# I dont know what blueprints do or why we separate them
notifications_bp = Blueprint('notifications', __name__)
frontend_bp = Blueprint('frontend', __name__)

# eBay API credentials and endpoint
# These should be stored securely and not hardcoded in production
# https://developer.ebay.com/marketplace-account-deletion
VERIFICATION_TOKEN = os.getenv('VERIFICATION_TOKEN')
ENDPOINT_URL = os.getenv('ENDPOINT_URL')

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
        

# Add a root route for the homepage
@frontend_bp.route('/')
def home():
    return """
    <h1>Welcome to the eBay Gold Scraper API!</h1>
    <p>Use the following endpoints:</p>
    <ul>
        <li><a href="/ebay/notifications">/ebay/notifications</a> - eBay notifications endpoint</li>
    </ul>
    """
