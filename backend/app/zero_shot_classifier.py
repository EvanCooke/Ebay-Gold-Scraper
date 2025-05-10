from transformers import pipeline
import re

# Regex patterns for weight and purity
weight_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(oz|grams|g)", re.IGNORECASE)
purity_pattern = re.compile(r"(\d{1,2})\s*(k|kt|karat)", re.IGNORECASE)

# Load the zero-shot classification pipeline
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# # consider using the 'metal' field in the ebay api response to filter out non-gold items as well
def classify_listing(row):

    """
    Classifies an eBay listing as authentic gold or not.

    Args:
        row (list): A row from the database containing listing details.
        labels (list): Labels for the zero-shot classifier.

    Returns:
        bool: True if the listing is authentic gold, False otherwise.
    """
    # Prepare input for the classifier
    input_text = f"{row[1]}, {row[2]}, Metal: {row[3]}, Total Carat Weight: {row[4]}, Metal Purity: {row[5]}"

    # # Check for forbidden terms, accounting for negations
    # forbidden_terms = ["gold plated", "gold filled", "gold tone", "testing kit", "testing needle", "testing solution", "testing acid", "testing pen", "testing kit"]
    # for term in forbidden_terms:
    #     if term in input_text and not re.search(rf"(not|no)\s+{term}", input_text, re.IGNORECASE):
    #         return False

    # Check if "gold" is mentioned
    if "gold" not in input_text.lower():
        return False
    
    # if "test" is in title, return False
    if "test" in row[1].lower():
        return False

    # Placeholder for regex validation (optional in this phase)
    weight_match = weight_pattern.search(input_text)
    purity_match = purity_pattern.search(input_text)
    # Uncomment the following lines if weight and purity are required
    # if not weight_match or not purity_match:
    #     return False

    # Define labels for zero-shot classification
    labels = [
        "authentic solid gold item",
        "not authentic solid gold item",
    ]

    # Classify using zero-shot classification
    try:
        classifier_result = classifier(input_text, labels)
        if classifier_result["labels"][0] == "authentic solid gold item" and classifier_result["scores"][0] > 0.49:
            return True
    except Exception as e:
        print(f"Error during classification: {e}")

    return False
    

def update_gold_column(conn):
    """
    Fetches rows from the ebay_listings table, classifies each row, and updates the 'is_gold' column.

    Args:
        conn: The database connection object.
    """
    cursor = conn.cursor()

    try:
        # Fetch all rows from the ebay_listings table
        query = "SELECT item_id, title, description, metal, total_carat_weight, metal_purity FROM ebay_listings;"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Classify each row and update the 'gold' column
        for row in rows:
            result = classify_listing(row)

            # Update the 'gold' column for the current row
            update_query = "UPDATE ebay_listings SET is_gold = %s WHERE item_id = %s;"
            cursor.execute(update_query, (result, row[0]))

        conn.commit()
        print("Updated 'gold' column for all rows in the ebay_listings table.")

    except Exception as e:
        conn.rollback()
        print(f"Error updating 'gold' column: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    pass