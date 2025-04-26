import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re

# Import the get_item_details function from ebay_search.py
from backend.ebay_search import get_item_details  # Import the function
from backend.ebay_search import MARKETPLACE_ID, access_token # Import these variables

# Define headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.ebay.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

# Define the eBay search URL
url = "https://www.ebay.com/sch/i.html"

# Define the query parameters for the search request
params = {
    "_from": "R40",  # Filter for US sellers
    "_nkw": "gold scrap jewelry",  # Search query
    "_sacat": "0",  # No category
    "_ipg": "240",  # Max items per page
    "LH_ReturnsAccepted": 1,  # Filter for sellers that accept returns
    "LH_RPA": "1",  # Filter for items with free returns
    "LH_BIN": "1"  # Filter for Buy It Now (non-auction) items only
}

# Initialize variables
items_list = []
item_counter = 0  # To track the current item number

try:
    # Initial request to get total items available
    response = requests.get(url, headers=headers, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract total number of items from the search results
    total_items_text = soup.find('h1', class_='srp-controls__count-heading').get_text(strip=True)

    # Use regex to find the number of total items
    total_items_match = re.search(r'(\d+)', total_items_text)
    if total_items_match:
        total_items = int(total_items_match.group(1))  # Get the first matched group as an integer
        print(f"Total items found for '{params['_nkw']}': {total_items}")
    else:
        print("Could not find total items count.")
        total_items = 0  # Default to 0 if not found

    # Loop over pages
    page_number = 0
    while True:
        page_number += 1;
        item_counter = 0  # Reset the item counter for each page
        item_counter_total = 0  # Track the total items processed
        print(f'\nScraping page: {page_number}')

        params['_pgn'] = page_number

        # Send the request to the search results page with headers
        response = requests.get(url, headers=headers, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the next button
        next_button = soup.find('button', class_='pagination__next', type='next')
        if next_button and next_button.get('aria-disabled') == 'true':
            print('No more pages to scrape')
            break

        # Extract items
        items = soup.find_all('div', class_='s-item__wrapper clearfix')
        total_items_on_page = len(items[2:])  # Exclude irrelevant first items

        for item in items[2:]:
            try:
                title = item.find('div', class_='s-item__title').text
                price = item.find('span', class_='s-item__price').text
                link = item.find('a', class_='s-item__link')['href'].split('?')[0]
                image_url = item.find('div', class_='s-item__image-wrapper image-treatment').find('img').get('src', 'No image URL')

                # Fetch description from item page
                # description = get_item_description(link)
                item_details = get_item_details(access_token, link, MARKETPLACE_ID) # use get_item_details
                description = item_details.get('description', None) if item_details else "Description not available"
                seller_username = item_details.get('seller', {}).get('username') if item_details else None
                seller_feedback_score = item_details.get('seller', {}).get('feedbackScore') if item_details else None
                feedback_percent = item_details.get('seller', {}).get('feedbackPercentage') if item_details else None
                shipping_options = item_details.get('shippingOptions') if item_details else None
                top_rated = item_details.get('topRatedBuyingExperience') if item_details else None
                returns_accepted = item_details.get('returnsAccepted') if item_details else None
                item_specifics_raw = item_details.get('localizedAspects', []) if item_details else None
                item_specifics = {}
                if item_specifics_raw:
                    for spec in item_specifics_raw:
                        name = spec.get('name')
                        value = spec.get('value')
                        if name and value:
                            item_specifics[name] = value
                

                # Increment the item counter
                item_counter += 1

                # Display the current progress on the same line
                print(f"\rProcessing item: {item_counter} (Page item: {item_counter_total} / {total_items_on_page})", end='', flush=True)

                # Store item data
                item_dict = {
                    'Title': title,
                    'Price': price,
                    'Link': link,
                    'Image Link': image_url,
                    'Description': description,
                    'seller_username': seller_username,
                    'seller_feedback_score': seller_feedback_score,
                    'feedback_percent': feedback_percent,
                    'shipping_options': shipping_options,
                    'top_rated_buying_experience': top_rated,
                    'returns_accepted': returns_accepted,
                    'item_specifics': item_specifics
                }
                items_list.append(item_dict)

                # Add a random delay to avoid detection
                time.sleep(random.uniform(1, 3))

                # if item_counter == 10:
                #     break

            except Exception as e:
                print(f"\nError extracting item: {e}")

except KeyboardInterrupt:
    print("\nScraping interrupted by user.")

print(f"\nTotal items scraped: {len(items_list)}")

# Create a DataFrame from the scraped data
items_df = pd.DataFrame(items_list)

# Remove the 'Image Link' column
items_df = items_df.drop('Image Link', axis=1)

# Define forbidden terms and filter results
forbidden_terms = [
    'gold filled',
    'gold plated',
    'gold tone'
]

mask = ~items_df['Title'].str.lower().str.contains(r'\b(?:' + '|'.join(forbidden_terms) + r')\b')
filtered_df = items_df[mask].reset_index(drop=True)

# Save to CSV
filtered_df.to_csv('search-results.csv', index=False, sep='¬|')

print(f"Filtered items saved to CSV. Total: {len(filtered_df)}")
