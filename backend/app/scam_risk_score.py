from openai import OpenAI
import tiktoken # OpenAI's tokenizer
import json
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')


MODEL_NAME = "gpt-3.5-turbo"
MAX_TOKENS_FOR_MODEL = 4096

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
No returns accepted can be a risk factor. 
Be cautious of listings where non gold items (such as Amethyst) are contributing to the weight and thus the profit

For each listing, provide your output as a JSON array, where each object contains:
- 'item_id'
- 'scam_risk_score'
- 'explanation': a brief justification (3-4 bullet points) for the assigned score.

Do not include any other text or explanations outside this JSON structure.
Example for two items:
[
  {"item_id": "123", "scam_risk_score": 2, "explanation": "High seller feedback. Price matches melt value."},
  {"item_id": "456", "scam_risk_score": 7, "explanation": "Low feedback. Price much lower than melt value."}
]

Here are the listings to analyze:
"""

TARGET_TOKENS_PER_BATCH = MAX_TOKENS_FOR_MODEL - (count_tokens(SYSTEM_PROMPT) + 500) # Reserve 500 for response

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

def clean_gpt_json_response(response):
    # Remove code block markers if present
    response = response.strip()
    if response.startswith("```"):
        response = re.sub(r"^```[a-zA-Z]*\n?", "", response)
        response = re.sub(r"```$", "", response)
    # Remove trailing commas before closing brackets
    response = re.sub(r",\s*\]", "]", response)
    return response

### -------------------------------https://www.youtube.com/watch?v=CHsRy4gl6hk-------------------------------------
def get_scam_scores_from_chatgpt(prompt):
    client = OpenAI(
        api_key=API_KEY,
    )

    response = client.responses.create(
        model= MODEL_NAME,
        input=prompt
    )

    return response.output_text

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
        current_batch = ""

        for row in rows:
            current_listing = format_listing_for_prompt(row)
            if count_tokens(current_batch + current_listing) < TARGET_TOKENS_PER_BATCH:
                current_batch += current_listing
            else:
                batches.append(current_batch)
                current_batch = current_listing
        
        # Add the last batch if it has listings
        if len(current_batch) > 0:
            batches.append(current_batch)

        # Process each batch with ChatGPT
        for batch in batches:
            # Call the ChatGPT API
            response = get_scam_scores_from_chatgpt(SYSTEM_PROMPT + batch)
            # Parse the JSON response
            
            if not response:
                print("No response from ChatGPT.")
            else:
                try:
                    # Attempt to parse the response as JSON
                    cleaned_response = clean_gpt_json_response(response)
                    scam_scores = json.loads(cleaned_response)

                    # Update the 'scam_risk_score' column for each item
                    for item in scam_scores:
                        update_query = """
                            UPDATE ebay_listings
                            SET scam_risk_score = %s,
                                scam_risk_score_explanation = %s
                            WHERE item_id = %s;
                        """
                        cursor.execute(update_query, (item['scam_risk_score'], item['explanation'], item['item_id']))
                except json.JSONDecodeError:
                    print(f"Failed to decode JSON response: {response}")
                                
        # Commit the changes to the database
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Error updating 'scam_risk_score' column: {e}")
    finally:
        cursor.close()