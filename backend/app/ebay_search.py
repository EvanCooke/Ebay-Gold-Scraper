import os # for .env file
from dotenv import load_dotenv # for loading environment variables
import base64 # for base64 encoding OAuth credentials
import requests # for HTTP requests
import json # for JSON parsing
import csv # for CSV file writing
import sys
import time # for sleep between requests
from urllib.parse import quote  # Import the quote function for URL encoding
from psycopg2.extras import Json  # For handling JSON data
from database import connect_to_db, insert_data 
from zero_shot_classifier import update_gold_column # Import the zero-shot classifier function


load_dotenv(override=True) # Load environment variables from .env file

# --- Configuration ---
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Sandbox
# TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token" 
# SEARCH_API_URL = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search' 
# ITEM_DETAILS_BASE_URL = 'https://api.sandbox.ebay.com/buy/browse/v1/item/'

#Production
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"  
SEARCH_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"  
ITEM_DETAILS_BASE_URL = "https://api.ebay.com/buy/browse/v1/item/"  


SEARCH_KEYWORDS = 'gold scrap jewelry' 
MARKETPLACE_ID = 'EBAY_US' 
RESULTS_PER_PAGE = 100
MAX_PAGES = 20
FILTER_RETURNS_ACCEPTED = False  # Set to True to filter for listings that accept returns
OUTPUT_CSV_FILENAME = 'ebay_gold_listings_browse_api.csv'
CATEGORY_IDS = None # Set to None to search all categories, or specify a list of category IDs
SELLER_FEEDBACK_MIN = 0 # Minimum feedback score for sellers (if needed)


DATABASE = os.environ.get('DB_NAME')
USER = os.environ.get('DB_USER')
PASSWORD = os.environ.get('DB_PASSWORD')
HOST = os.environ.get('DB_HOST')
PORT = os.environ.get('DB_PORT')


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
        

    #THIS IS WEIRD!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!    
    if returns_accepted is not None:
        if 'filter' in params:
            params['filter'] += f",returnsAccepted:[{str(returns_accepted).lower()}]"
        else:
            params['filter'] = f"returnsAccepted:[{str(returns_accepted).lower()}]"
        print(f"  Filtering for returns accepted: {returns_accepted}")

    # # print the full URL being requested for debugging purposes
    # full_url_with_params = requests.Request('GET', SEARCH_API_URL, headers=headers, params=params).prepare().url
    # print(f"Request URL: {full_url_with_params}") # Print the full URL

    try:
        response = requests.get(SEARCH_API_URL, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        listings_data = response.json() 
        total_listings = listings_data.get('total', 0)
        item_summaries = listings_data.get('itemSummaries', []) # does not contain description or returnsAccepted, etc.
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
def get_item_details(access_token, item_id, marketplace_id, max_retries=1, retry_delay=1):
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

    for attempt in range(max_retries):
        try:
            response = requests.get(details_url, headers=headers, params=params, timeout=15)
            response.raise_for_status() # Raise an exception for HTTP errors

            
            item_details = response.json()

            # Extract prioritized details
            extracted_details = {
                'description': item_details.get('description'),
                'metal': None,
                'returns_accepted': None,
                'item_specifics': None  # Initialize
            }

            # VERY SUSPICIOUS__________----------------------------------________________-----------------____--_-_-__---_--
            # Extract metal from localizedAspects
            localized_aspects = item_details.get('localizedAspects', [])

            # Extract returnsAccepted
            return_terms = item_details.get('returnTerms', {})
            extracted_details['returns_accepted'] = return_terms.get('returnsAccepted')

            # Extract item specifics - build a dictionary
            item_specifics_dict = {}
            for aspect in localized_aspects:
                name = aspect.get('name', '').lower()  # Safe access, case-insensitive
                if name == 'metal':  # Safe access, case-insensitive
                    extracted_details['metal'] = aspect.get('value')
                elif name == 'total carat weight':
                    extracted_details['total_carat_weight'] = aspect.get('value')
                elif name == 'metal purity':
                    extracted_details['metal_purity'] = aspect.get('value')
                else: 
                    item_specifics_dict[aspect.get('name')] = aspect.get('value')
            extracted_details['item_specifics'] = item_specifics_dict
            #__________----------------------------------________________-----------------____--_-_-__---_--

            return extracted_details

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

    # Add a flag to stop after one item
    stop_after_one_item = 0

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
            seller_info = summary.get('seller', {})
            item_id = summary.get('itemId')
            item_details = get_item_details(access_token, item_id, MARKETPLACE_ID)
            
            all_item_data.append({
                'item_id': summary.get('itemId'),
                'title': summary.get('title'),
                'price': summary.get('price', {}).get('value'),
                'currency': summary.get('price', {}).get('currency'),
                'seller_username': seller_info.get('username'),
                'seller_feedback_score': seller_info.get('feedbackScore'),
                'feedback_percent': seller_info.get('feedbackPercentage'),
                'image_url': summary.get('image', {}).get('imageUrl'),
                'item_url': summary.get('itemWebUrl'),
                'shipping_options': summary.get('shippingOptions', None),
                'top_rated_buying_experience': summary.get('topRatedBuyingExperience'),
                'description': item_details.get('description', None),
                'returns_accepted': item_details.get('returns_accepted', None),
                'metal': item_details.get('metal', None),
                'total_carat_weight': item_details.get('total_carat_weight', None),
                'metal_purity': item_details.get('metal_purity', None),
                'item_specifics': item_details.get('item_specifics', {}),  # Store as JSON string for CSV'
            })
            stop_after_one_item += 1
            # Stop after processing one item
            if stop_after_one_item >= 10:
                print("Stopping after processing 20 items for testing.")
                break

            # time.sleep(0.5)  # Be mindful of rate limits

        
        # Break the outer loop if testing with one item
        if stop_after_one_item >= 10:
            break

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
    conn = connect_to_db()
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

    print("updating gold column...")
    # Update the 'gold' column using the zero-shot classifier
    update_gold_column(conn)

    # Close the database connection
    conn.close()
    print("Database connection closed.")


    # NEED TO PROVIDE itemSummaries.itemAffiliateWebUrl to user to get money for affiliate links

    # eBay Partner Network: In order to be commissioned for your sales, you must use the URL returned 
    # in the itemAffiliateWebUrl field to forward your buyer to the ebay.com site.