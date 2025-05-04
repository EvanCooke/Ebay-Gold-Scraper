from transformers import pipeline

# Load the zero-shot classification pipeline
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# # consider using the 'metal' field in the ebay api response to filter out non-gold items as well
# def classify_listing(row):

#     # Extract title and description from the row
#     print(row)
#     title = row[1]
#     description = row[11]

#     # Combine title and description for classification
#     text = title + " " + description
#     candidate_labels = ["gold", "non-gold"]

#     # Perform zero-shot classification
#     result = classifier(text, candidate_labels)
#     return result["labels"][0] == "gold"

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
            # Perform zero-shot classification
            classifier_result = classifier(row[1] + ", Metal: " + row[3] + ", " + row[2],  ["authentic solid gold item", "non-gold or fake or gold-plated item"])
            # is_gold = classifier_result["labels"][0] == "authentic solid gold item"

            # my attempt at making zero shot classifier more accurate, may have to use regex instead of python string methods
            if classifier_result["labels"][0] == "authentic solid gold item" and "gold" in row[3].lower():
                is_gold = True
            else:
                is_gold = False

            # Update the 'gold' column for the current row
            update_query = "UPDATE ebay_listings SET is_gold = %s WHERE item_id = %s;"
            cursor.execute(update_query, (is_gold, row[0]))

        conn.commit()
        print("Updated 'gold' column for all rows in the ebay_listings table.")

    except Exception as e:
        conn.rollback()
        print(f"Error updating 'gold' column: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    pass