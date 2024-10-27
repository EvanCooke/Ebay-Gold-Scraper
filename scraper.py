import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

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
    "_from": "R40", # Filter for US sellers
    "_nkw": "gold scrap jewelry", # Search query
    "_sacat": "0", # No category
    "_ipg": "240",  # Max items per page
    'rt': 'nc', # No auctions
    "LH_ReturnsAccepted": 1, # Filter for sellers that accept returns
    "LH_RPA": "1",  # Filter for items with free returns
    # "LH_Authenticity": "1",  # Adding authenticity guarantee filter
}

# Create a function to get item description from the item page
def get_item_description(item_url):
    try:
        response = requests.get(item_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        description = soup.find('div', {'id': 'viTabs_0_is'}).get_text(strip=True)
        return description
    except Exception as e:
        print(f"Failed to get description from {item_url}: {e}")
        return "Description not available"

# Initialize variables
page_number = 0
items_list = []
item_counter = 0  # To track the current item number
page_item_counter = 0

# Loop over pages
while True:
    page_number += 1
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
            description = get_item_description(link)

            # Increment the item counter
            item_counter += 1
            page_item_counter += 1

            # Display the current progress on the same line
            print(f"\rProcessing item: {item_counter} (Page item: {page_item_counter} / {total_items_on_page})", end='', flush=True)

            # Store item data
            item_dict = {
                'Title': title,
                'Price': price,
                'Link': link,
                'Image Link': image_url,
                'Description': description
            }
            items_list.append(item_dict)

            # Add a random delay to avoid detection
            time.sleep(random.uniform(1, 3))
            if page_item_counter == 10:
                page_item_counter = 0
                break
        except Exception as e:
            print(f"\nError extracting item: {e}")

    

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
filtered_df.to_csv('search-results.csv', index=False, sep='¬')

print(f"Filtered items saved to CSV. Total: {len(filtered_df)}")
