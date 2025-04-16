import os # for .env file
from dotenv import load_dotenv # for loading environment variables
import base64 # for base64 encoding OAuth credentials
import requests # for HTTP requests
import json # for JSON parsing
import csv # for CSV file writing
import time # for sleep between requests

load_dotenv() # Load environment variables from .env file

# --- Configuration ---
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" # sandbox or production
SEARCH_API_URL = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search' # Sandbox
ITEM_DETAILS_BASE_URL = 'https://api.sandbox.ebay.com/buy/browse/v1/item/' # Sandbox

SEARCH_KEYWORDS = '"gold jewlery" | "scrap gold" | "gold estate" | electronics | item'
MARKETPLACE_ID = 'EBAY_US' 
RESULTS_PER_PAGE = 100
MAX_PAGES = 20
FILTER_RETURNS_ACCEPTED = False  # Set to True to filter for listings that accept returns
OUTPUT_CSV_FILENAME = 'ebay_gold_listings_browse_api.csv'
CATEGORY_IDS = None # Set to None to search all categories, or specify a list of category IDs
SELLER_FEEDBACK_MIN = 0 # Minimum feedback score for sellers (if needed)


# --- Function to Obtain Access Token ---
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
    

# --- Function to Search eBay Listings ---
def search_ebay_listings(access_token, search_query, category_ids, limit, marketplace_id, filter_str=None, sort_order=None, returns_accepted=None):
    """
    Searches eBay listings using the /item_summary/search endpoint.
    See: https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
    See (for filters): https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html
    See (for sorting): https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-request-parameters.html#Parameter-sort
    """
    if not access_token:
        print("Cannot search listings without an access token.")
        return None

    print(f"\nSearching eBay marketplace '{marketplace_id}' for '{search_query}'...")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-EBAY-C-MARKETPLACE-ID': marketplace_id,
        'Accept': 'application/json'
    }
    params = {
        'q': search_query,
        'limit': limit
    }
    if filter_str:
        params['filter'] = filter_str
        print(f"  Applying filter: '{filter_str}'")
        
    if returns_accepted is not None:
        if 'filter' in params:
            params['filter'] += f",returnsAccepted:[{str(returns_accepted).lower()}]"
        else:
            params['filter'] = f"returnsAccepted:[{str(returns_accepted).lower()}]"
        print(f"  Filtering for returns accepted: {returns_accepted}")

    
    try:
        response = requests.get(SEARCH_API_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        listings_data = response.json()
        total_listings = listings_data.get('total', 0)
        item_summaries = listings_data.get('itemSummaries', [])
        print(f"Search successful! Found {total_listings} potential listings (returning {len(item_summaries)} on this page).")
        return item_summaries, total_listings
    except requests.exceptions.RequestException as e:
        print(f"Error searching listings: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response text: {e.response.text}")
        return None, 0

# --- Function to Get Item Details ---
def get_item_details(access_token, item_id, marketplace_id):
    """
    Retrieves detailed information for a specific item using the /item/{item_id} endpoint.
    See: https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem
    See (for field groups): https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-request-parameters.html#Parameter-fieldgroups
    """
    if not access_token or not item_id:
        print("Access token and item ID are required to fetch details.")
        return None

    details_url = f"{ITEM_DETAILS_BASE_URL}{item_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-EBAY-C-MARKETPLACE-ID': marketplace_id,
        'Accept': 'application/json'
    }
    params = {
        'fieldgroups': 'description,itemSpecifics,seller'  # Request description, specifics, and seller info
    }

    print(f"  Fetching details for Item ID: {item_id}...")
    try:
        response = requests.get(details_url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        item_details = response.json()
        return item_details
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching details for item {item_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response status code: {e.response.status_code}")
            try:
                error_details = e.response.json()
                print(f"  Error details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"  Response text: {e.response.text}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
    if not access_token:
        exit("Failed to get access token. Exiting.")

    # --- Construct Search Filters ---
    search_filters = []
    if SELLER_FEEDBACK_MIN > 0:
        search_filters.append(f"feedbackScoreMin:[{SELLER_FEEDBACK_MIN}]")
    FILTER_STRING = ",".join(search_filters) if search_filters else None

    all_item_data = []
    total_fetched = 0
    page_number = 1

    while page_number <= MAX_PAGES:
        item_summaries, total_listings = search_ebay_listings(
            access_token=access_token,
            search_query=SEARCH_KEYWORDS,
            category_ids=CATEGORY_IDS,
            limit=RESULTS_PER_PAGE,
            marketplace_id=MARKETPLACE_ID,
            filter_str=FILTER_STRING
            # You can add a sort order here if needed, e.g., sort_order='PricePlusShippingLowest'
        )

        if not item_summaries:
            print("No item summaries found on this page or search failed.")
            break

        for summary in item_summaries:
            item_id = summary.get('itemId')
            title = summary.get('title')
            price = summary.get('price', {}).get('value')
            currency = summary.get('price', {}).get('currency')
            seller_username = summary.get('seller', {}).get('username')
            seller_feedback_score = summary.get('seller', {}).get('feedbackScore')

            item_details = get_item_details(access_token, item_id, MARKETPLACE_ID)
            description = item_details.get('description') if item_details else None
            item_specifics_raw = item_details.get('localizedAspects') if item_details else None
            item_specifics = {}
            if item_specifics_raw:
                for spec in item_specifics_raw:
                    name = spec.get('name')
                    value = spec.get('value')
                    if name and value:
                        item_specifics[name] = value

            all_item_data.append({
                'item_id': item_id,
                'title': title,
                'price': price,
                'currency': currency,
                'seller_username': seller_username,
                'seller_feedback_score': seller_feedback_score,
                'description': description,
                'item_specifics': json.dumps(item_specifics)  # Store as JSON string for CSV
            })
            time.sleep(0.5)  # Be mindful of rate limits

        total_fetched += len(item_summaries)
        if total_fetched >= total_listings or page_number >= MAX_PAGES:
            break
        page_number += 1
        print(f"Moving to page {page_number}...")

    # --- Write to CSV ---
    if all_item_data:
        print(f"\nWriting {len(all_item_data)} items to {OUTPUT_CSV_FILENAME}...")
        with open(OUTPUT_CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['item_id', 'title', 'price', 'currency', 'seller_username', 'seller_feedback_score', 'description', 'item_specifics']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_item_data)
        print("Data written to CSV file.")
    else:
        print("No data fetched to write to CSV.")