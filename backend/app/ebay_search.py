import os # for .env file
from dotenv import load_dotenv # for loading environment variables
import base64 # for base64 encoding OAuth credentials
import requests # for HTTP requests
import json # for JSON parsing
import csv # for CSV file writing
import time # for sleep between requests
from urllib.parse import quote  # Import the quote function for URL encoding
from psycopg2.extras import Json  # For handling JSON data
from backend.app.database import connect_to_db, insert_data 
from instance.config import Config  # Import Config class


load_dotenv() # Load environment variables from .env file

# --- Configuration ---
CLIENT_ID = Config.CLIENT_ID
CLIENT_SECRET = Config.CLIENT_SECRET
TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" # sandbox or production
SEARCH_API_URL = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search' # Sandbox
ITEM_DETAILS_BASE_URL = 'https://api.sandbox.ebay.com/buy/browse/v1/item/' # Sandbox

SEARCH_KEYWORDS = 'gold'
MARKETPLACE_ID = 'EBAY_US' 
RESULTS_PER_PAGE = 100
MAX_PAGES = 20
FILTER_RETURNS_ACCEPTED = False  # Set to True to filter for listings that accept returns
OUTPUT_CSV_FILENAME = 'ebay_gold_listings_browse_api.csv'
CATEGORY_IDS = None # Set to None to search all categories, or specify a list of category IDs
SELLER_FEEDBACK_MIN = 0 # Minimum feedback score for sellers (if needed)

DATABASE = Config.DB_NAME
USER = Config.DB_USER
PASSWORD = Config.DB_PASSWORD
HOST = Config.DB_HOST
PORT = Config.DB_PORT


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

    # print the full URL being requested for debugging purposes
    full_url_with_params = requests.Request('GET', SEARCH_API_URL, headers=headers, params=params).prepare().url
    print(f"Request URL: {full_url_with_params}") # Print the full URL

    try:
        response = requests.get(SEARCH_API_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        listings_data = response.json() 
        # print("listings data: ", listings_data)
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
def get_item_details(access_token, item_id, marketplace_id, max_retries=0, retry_delay=1):
    """
    Retrieves detailed information for a specific item using the /item/{item_id} endpoint.
    See: https://developer.ebay.com/api-docs/buy/browse/resources/item/methods/getItem
    See (for field groups): https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-request-parameters.html#Parameter-fieldgroups
    """
    if not access_token or not item_id:
        print("Access token and item ID are required to fetch details.")
        return None

    # details_url = f"{ITEM_DETAILS_BASE_URL}{item_id}" # Use the item_id directly
    details_url = f"{ITEM_DETAILS_BASE_URL}{quote(item_id)}" # correctly encode item ID


    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-EBAY-C-MARKETPLACE-ID': marketplace_id,
        'X-EBAY-C-ENDUSERCTX': 'contextualLocation=country%3DUS%2Czip%3D19406', # Add the required header
        'Accept': 'application/json',
    }
    params = {
        'fieldgroups': 'PRODUCT,ADDITIONAL_SELLER_DETAILS'
    }

    print(f"  Fetching details for Item ID: {item_id}...")

    print(f"  Request URL: {details_url}") # Print the full URL

    for attempt in range(max_retries):
        try:
            response = requests.get(details_url, headers=headers, params=params, timeout=15)
            response.raise_for_status() # Raise an exception for HTTP errors

            # Check rate limit headers
            rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 1))  # Default to 1 if missing
            reset_time = int(response.headers.get('X-RateLimit-Reset', 60))  # Default to 60 seconds if missing

            # If rate limit is about to be exceeded, pause
            if rate_limit_remaining == 0:
                print(f"Rate limit reached. Waiting for {reset_time} seconds...")
                time.sleep(reset_time)

            # Parse and return item details
            item_details = response.json()
            return item_details

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching details for item {item_id} (Attempt {attempt + 1}/{max_retries}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Response status code: {e.response.status_code}")
                try:
                    error_details = e.response.json()
                    print(f"  Error details: {json.dumps(error_details, indent=2)}")
                    if e.response.status_code != 500: # Don't retry if it's a different client error
                        break
                except json.JSONDecodeError:
                    print(f"  Response text: {e.response.text}")
                    if e.response.status_code != 500:
                        break

            # Retry logic
            if attempt < max_retries - 1:
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"  Max retries reached for item {item_id}. Skipping.")
                return None
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

        # Add the snippet here to exit the loop if no listings are found
        if total_listings == 0 or not item_summaries:
            print("No more listings found. Exiting pagination loop.")
            break

        for summary in item_summaries:
            item_id = summary.get('itemId')
            title = summary.get('title')
            price = summary.get('price', {}).get('value')
            currency = summary.get('price', {}).get('currency')
            seller_info = summary.get('seller', {})
            seller_username = seller_info.get('username')
            seller_feedback_score = seller_info.get('feedbackScore')
            feedback_percent = seller_info.get('feedbackPercentage')
            image_url = summary.get('image', {}).get('imageUrl')
            item_url = summary.get('itemWebUrl')
            shipping_options = summary.get('shippingOptions')
            top_rated = summary.get('topRatedBuyingExperience')

            item_details = get_item_details(access_token, item_id, MARKETPLACE_ID)
            description = item_details.get('description', None) if item_details else None # are following if statements needed?
            returns_accepted_flag = item_details.get('returnsAccepted', None) if item_details else None
            print(f"  Returns accepted: {returns_accepted_flag}")
            item_specifics_raw = item_details.get('localizedAspects', []) if item_details else None
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
                'feedback_percent': feedback_percent,
                'image_url': image_url,
                'item_url': item_url,
                'shipping_options': shipping_options if shipping_options else None,
                'top_rated_buying_experience': top_rated,
                'description': description,
                'returns_accepted': returns_accepted_flag,
                'item_specifics': item_specifics  # Store as JSON string for CSV
            })

            time.sleep(0.5)  # Be mindful of rate limits
            

        total_fetched += len(item_summaries)
        if total_fetched >= total_listings or page_number >= MAX_PAGES:
            break
        page_number += 1
        print(f"Moving to page {page_number}...")

    # --- Write to CSV ---
    # if all_item_data:
    #     print(f"\nWriting {len(all_item_data)} items to {OUTPUT_CSV_FILENAME}...")
    #     with open(OUTPUT_CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
    #         fieldnames = ['item_id', 'title', 'price', 'currency', 'seller_username', 'seller_feedback_score', 'feedback_percent', 'image_url', 'item_url', 'shipping_options', 'top_rated_buying_experience', 'description', 'returns_accepted', 'item_specifics']
    #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #         writer.writeheader()
    #         writer.writerows(all_item_data)
    #     print("Data written to CSV file.")
    # else:
    #     print("No data fetched to write to CSV.")

    # Establish a connection to the database
    conn = connect_to_db(DATABASE, USER, PASSWORD, HOST, PORT)
    if not conn:
        exit("Failed to connect to the database. Exiting.")

    # --- Insert data into PostgreSQL database ---
    if all_item_data:
        print(f"\nInserting {len(all_item_data)} items into the database...")
        for item in all_item_data:
            success = insert_data(conn, "ebay_listings", item)
            if success:
                print(f"Inserted item {item['item_id']} successfully.")
            else:
                print(f"Failed to insert item {item['item_id']}.")
    else:
        print("No data fetched to insert into the database.")

    # Close the database connection
    conn.close()
    print("Database connection closed.")


    # NEED TO PROVIDE itemSummaries.itemAffiliateWebUrl to user to get money for affiliate links

    # eBay Partner Network: In order to be commissioned for your sales, you must use the URL returned 
    # in the itemAffiliateWebUrl field to forward your buyer to the ebay.com site.