import openai
import tiktoken # OpenAI's tokenizer
import json

MODEL_NAME = "gpt-3.5-turbo"
MAX_TOKENS_FOR_MODEL = 4096
TARGET_TOKENS_PER_BATCH = MAX_TOKENS_FOR_MODEL - 500 # Reserve 2000 for response

encoding = tiktoken.encoding_for_model(MODEL_NAME)

def count_tokens(text):
    return len(encoding.encode(text))

# Base prompt structure (tokens for this will be constant per batch)
SYSTEM_PROMPT = """
You are an expert eBay gold listing analyzer. Your task is to assess the "scam risk score" for each provided listing.
The score should be an integer between 0 (very low risk) and 10 (very high risk).
Consider all provided attributes: item_id, title, price, seller_feedback_score, feedback_percent, top_rated_buying_experience, description, returns_accepted, melt_value, profit.
A high profit margin compared to melt value might be a red flag, unless justified by rarity or craftsmanship.
Low seller feedback, poor feedback percentage, or lack of top-rated status can increase risk.
Vague or copied descriptions, or descriptions that don't match the title/images (if you had images), are risky.
Extremely low prices for the supposed weight/purity are suspicious.
No returns accepted can be a minor risk factor.

Provide your output as a JSON array, where each object in the array contains only 'item_id' and 'scam_risk_score'. Do not include any other text or explanations outside this JSON structure.
Example for two items:
[
  {"item_id": "123", "scam_risk_score": 2},
  {"item_id": "456", "scam_risk_score": 7}
]

Here are the listings to analyze:
"""

# Helper function to format a single listing
def format_listing_for_prompt(row):
    # Be mindful of very long descriptions. You might need to truncate them if they alone are too big.
    # Consider what's most important in the description.
    # Example: Truncate description if it's excessively long
    max_desc_length = 1000 # characters, adjust as needed
    description = row[6]
    if len(description) > max_desc_length:
        description = description[:max_desc_length] + "..."

    return (
        f"Item ID: {row[0]}\n"
        f"Title: {row[1]}\n"
        f"Price: ${row[2]:.2f}\n"
        f"Seller Feedback Score: {row[3]}\n"
        f"Feedback Percent: {row[4]}%\n"
        f"Top Rated Buying Experience: {'Yes' if row[5] else 'No'}\n"
        f"Returns Accepted: {'Yes' if row[7] else 'No'}\n"
        f"Melt Value: ${row[8]:.2f}\n"
        f"Potential Profit: ${row[9]:.2f}\n"
        f"Description: {description}\n"
        f"---\n" # Separator between items
    )


def get_scam_scores_from_chatgpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def update_scam_risk_score_column(conn):
    cursor = conn.cursor()

    try:
        # Fetch all rows from the ebay_listings table
        query = """
        SELECT 
        
        item_id, title, price, seller_feedback_score, feedback_percent, 
        top_rated_buying_experience, description, returns_accepted, melt_value, profit

        FROM ebay_listings
        WHERE is_gold = TRUE
            AND profit IS NOT NULL
            AND melt_value IS NOT NULL;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # generate batches of prompts for processing with GPT
        batches = []
        current_batch = SYSTEM_PROMPT

        for row in rows:
            current_listing = format_listing_for_prompt(row)
            if count_tokens(current_batch + current_listing) < TARGET_TOKENS_PER_BATCH:
                current_batch += current_listing
            else:
                batches.append(current_batch)
                current_batch = SYSTEM_PROMPT + current_listing
        
        # Add the last batch if it has listings
        if count_tokens(current_batch) > count_tokens(SYSTEM_PROMPT):
            batches.append(current_batch)

        # Process each batch with ChatGPT
        for batch in batches:
            # Call the ChatGPT API
            response = get_scam_scores_from_chatgpt(batch)
            # Parse the JSON response
            scam_scores = json.loads(response)

            # Update the 'scan_risk_score' column for each item
            for item in scam_scores:
                update_query = """
                    UPDATE ebay_listings
                    SET scan_risk_score = %s
                    WHERE item_id = %s;
                """
                cursor.execute(update_query, (item['scam_risk_score'], item['item_id']))

    except Exception as e:
        conn.rollback()
        print(f"Error updating 'scan_risk_score' column: {e}")
    finally:
        cursor.close()