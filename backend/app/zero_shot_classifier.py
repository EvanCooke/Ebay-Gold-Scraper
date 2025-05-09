# ---------------------------------------------------------------------------------------------------------
# Check item_specifics for "Total Carat Weight" / "Metal Purity (/ "Metal" ???)".

# If present, normalize values (e.g. strip “carats”, convert to float) and write directly to your total_carat_weight and metal_purity columns.

# If absent, concatenate title + description into a single text blob.

# Run regex over text first:

# python
# Copy
# Edit
# for m in weight_pattern.finditer(text):
#     # convert oz → grams, collect (value, span)
# for m in purity_pattern.finditer(text):
#     # collect purity spans
# ``` :contentReference[oaicite:10]{index=10}.  
# Pass text into a spaCy pipeline with an EntityRuler (or Matcher) using your regex patterns for “WEIGHT” and “PURITY” 
# Python Humanities
# spaCy
# .

# Merge & dedupe: prefer exact regex matches; use spaCy-only matches for edge cases.

# Normalize numeric strings → float, units standardized (g), and assign to your metadata fields.
# ---------------------------------------------------------------------------------------------------------

from transformers import pipeline

# Load the zero-shot classification pipeline
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# # consider using the 'metal' field in the ebay api response to filter out non-gold items as well
def classify_listing(row):

    # Perform zero-shot classification
    metal = row[3] if row[3] else ""
    classifier_result = classifier(row[1] + ", Metal: " + metal + ", " + row[2],  ["authentic solid gold item", "non-gold or fake or gold-plated item"])
    # is_gold = classifier_result["labels"][0] == "authentic solid gold item"

    # if no metal is provided, assume it is listed gold
    # if metal is listed but not listed gold, assume it is not gold
    authentic_gold_terms = ["gold", "alloy", "unknown", "null"]
    contains_gold = metal.lower() in authentic_gold_terms or row[3] is None

    # my attempt at making zero shot classifier more accurate, may have to use regex instead of python string methods
    if classifier_result["labels"][0] == "authentic solid gold item" and contains_gold:
        return True
    else:
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
        query = "SELECT item_id, title, description, metal FROM ebay_listings;"
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