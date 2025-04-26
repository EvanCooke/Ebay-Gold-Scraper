import hashlib
from flask import Blueprint, request, jsonify

notifications_bp = Blueprint('notifications', __name__)

# Set these yourself
VERIFICATION_TOKEN = "your_verification_token_here"
ENDPOINT_URL = "https://yourdomain.com/ebay/notifications"

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
        
        return jsonify({"error": "No challenge_code provided"}), 400

    elif request.method == 'POST':
        # Handle actual notifications
        try:
            data = request.get_json()
            print("Received eBay Notification:", data)
            return jsonify({"message": "Notification received successfully"}), 200
        except Exception as e:
            print("Error processing notification:", str(e))
            return jsonify({"error": "Failed to process notification"}), 500
