import os # for .env file
import base64 # for base64 encoding OAuth credentials
import requests # for HTTP requests
import json # for JSON parsing

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

# Need to configure three parts of a client credentials grant request:
    # 1. The target endpoint
    # 2. The HTTP request headers
    # 3. The request payload
# https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html

# Sandbox: https://api.sandbox.ebay.com/identity/v1/oauth2/token
# Production: https://api.ebay.com/identity/v1/oauth2/token
TARGET_ENDPOINT = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

def get_access_token(client_id, client_secret, target_endpoint):
    """
    Obtains an OAuth access token from eBay using Client Credentials Grant.
    """
    print("Requesting Access Token...")

    try:
        # Set the following HTTP request headers:
            # Content-Type – Must be set to: application/x-www-form-urlencoded
            # Authorization – The word "Basic " followed by your Base64-encoded OAuth credentials (<client_id>:<client_secret>).
            # Prepare credentials for Basic Auth: base64(client_id:client_secret)
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {encoded_credentials}'
        }

        # Format the payload of your POST request with the following values:
        # Set grant_type to client_credentials.
            # Set scope to the URL-encoded space-separated list of the scopes needed for the 
            # interfaces you call with the access token.
        payload = {
                'grant_type': 'client_credentials',
                # Define the scope(s) your application needs. Check eBay documentation.
                # Example scope for buying APIs
                'scope': 'https://api.ebay.com/oauth/api_scope'
                # For different APIs or scopes, adjust this value.
                # Example: 'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly'
        }

        response = requests.post(target_endpoint, headers=headers, data=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        token_data = response.json()
        access_token = token_data.get('access_token')

        if not access_token:
                print("Error: Could not retrieve access token.")
                print("Response:", response.text)
                return None
        
        print("Access Token obtained successfully!")
        # Optional: print("Token:", access_token) # Be careful printing tokens
        # Optional: print("Expires in:", token_data.get('expires_in'), "seconds")
        
        return access_token
    
    # ??? Learn what this does
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during token retrieval: {e}")
        return None
    

def search_ebay_listings(access_token, api_url, search_term, limit=10):
    """
    Searches for eBay listings using the obtained access token.
    """
    if not access_token:
        print("Cannot search listings without an access token.")
        return None

    print(f"\nSearching eBay for '{search_term}'...")
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            # Add other necessary headers specified by the eBay API documentation
            # e.g., Marketplace ID: 'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }

        params = {
            'q': search_term, # The keyword to search for
            'limit': limit      # Number of items to return
            # Add other parameters as needed (e.g., category_ids, filter)
            # Refer to the specific eBay API documentation for available parameters
        }

        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status() # Raise an exception for bad status codes

        listings_data = response.json()
        print("Search successful!")
        return listings_data

    except requests.exceptions.RequestException as e:
        print(f"Error searching listings: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            # eBay often returns detailed error messages in the JSON body
            try:
                 error_details = e.response.json()
                 print(f"Error details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                 print(f"Response text: {e.response.text}") # Fallback if not JSON
        return None
    except Exception as e:
        print(f"An unexpected error occurred during search: {e}")
        return None
