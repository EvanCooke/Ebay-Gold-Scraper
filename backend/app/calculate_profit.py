import requests
import json

def get_gold_price_per_gram():
    """
    Retrieves gold price data from a given endpoint, parses the JSON response,
    and calculates the price of gold per gram in USD, using the average of the
    bid and ask prices from the 'prime' spread profile.

    Args:
        endpoint_url (str): The URL of the API endpoint that returns the gold price data in JSON format.
                           The JSON is expected to contain a structure similar to the example provided,
                           with 'bids' and 'asks' arrays within a 'payload' object.

    Returns:
        float: The calculated price of gold per gram in USD, or None if the request fails or
               the JSON structure is not as expected.  Returns the price rounded to 2 decimals.

    Raises:
        requests.exceptions.RequestException: If the HTTP request to the endpoint fails.
        json.JSONDecodeError: If the response from the endpoint is not valid JSON.
        KeyError: If the expected keys ('payload', 'bids', 'asks') are not found in the JSON data.
        TypeError: If the bid or ask prices are not numeric.
        ValueError: If the bid or ask price is invalid.
    """
    try:
        endpoint_url = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"

        # Send a GET request to the specified endpoint
        response = requests.get(endpoint_url)

        # Raise an exception if the request was not successful (e.g., 404, 500)
        response.raise_for_status()  # This is crucial for proper error handling

        # Parse the JSON response
        data = response.json()

        # Extract the first element of the response (list)
        first_entry = data[0]

        # Extract the 'spreadProfilePrices' key and find the 'prime' spread profile
        spread_profiles = first_entry["spreadProfilePrices"]
        prime_profile = next(profile for profile in spread_profiles if profile["spreadProfile"] == "prime")

        # Extract bid and ask prices
        prime_bid_price = prime_profile["bid"]
        prime_ask_price = prime_profile["ask"]

        # Calculate the average price
        price_per_troy_ounce = (prime_bid_price + prime_ask_price) / 2

        # Convert troy ounce to grams (1 troy ounce ≈ 31.1034768 grams)
        grams_per_troy_ounce = 31.1034768
        price_per_gram = price_per_troy_ounce / grams_per_troy_ounce

        return round(price_per_gram, 2)  # Round to 2 decimal places

    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to retrieve data from the endpoint: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response: {e}")
        return None
    except KeyError as e:
        print(f"Error: Missing key in JSON data: {e}")
        return None
    except TypeError as e:
        print(f"Error: Invalid data type: {e}")
        return None
    except ValueError as e:
        print(f"Error: Invalid value: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected exceptions
        print(f"An unexpected error occurred: {e}")
        return None

def calculate_profit(row, current_gold_price):
    price, weight, purity = float(row[1]), row[2], row[3]

    melt_value = (purity / 24) * weight * current_gold_price
    profit = melt_value - price

    return round(melt_value, 2), round(profit, 2)

def update_profit_column(conn):
    cursor = conn.cursor()

    try:
        # Fetch all rows from the ebay_listings table
        query = """
        SELECT item_id, price, weight, purity
        FROM ebay_listings
        WHERE is_gold = TRUE
            AND weight IS NOT NULL
            AND purity IS NOT NULL;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        current_gold_price = get_gold_price_per_gram()
        if current_gold_price is None:
            print("Failed to retrieve the current gold price. Exiting.")
            return

        # Calculate profit for each row and update the 'profit' column
        for row in rows:
            # Calculate melt value and profit
            melt_value, profit = calculate_profit(row, current_gold_price)

            # Update the 'profit' and 'melt_value' columns for the current row
            update_query = """
                UPDATE ebay_listings
                SET profit = %s, melt_value = %s
                WHERE item_id = %s;
            """
            cursor.execute(update_query, (profit, melt_value, row[0]))

        conn.commit()
        print("Updated 'profit' column for all rows in the ebay_listings table.")

    except Exception as e:
        conn.rollback()
        print(f"Error updating 'profit' column: {e}")
    finally:
        cursor.close()