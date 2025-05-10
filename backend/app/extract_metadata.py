# ---------------------------------------------------------------------------------------------------------
# Check item_specifics for "Total Carat Weight" / "Metal Purity (/ "Metal" ???)".

# If present, normalize values (e.g. strip “carats”, convert to float) and write directly to your total_carat_weight and metal_purity columns.

# If absent, concatenate title + description into a single text blob.

# Run regex over text first

# Merge & dedupe: prefer exact regex matches; use spaCy-only matches for edge cases.

# Normalize numeric strings → float, units standardized (g), and assign to your metadata fields.


# Check item_specifics for Metadata:

# 1
# Prioritize structured data from item_specifics (e.g., "Total Carat Weight", "Metal Purity", "Metal").
# Normalize values (e.g., strip units like "carats" or "grams", convert to floats).
# Fallback to Unstructured Data:

# 2
# If item_specifics is missing or incomplete, concatenate the title and description into a single text blob.
# Use regex to extract weight and purity from the text.
# Merge and Deduplicate:

# 3
# Prefer exact matches from regex over NLP-based matches (e.g., spaCy).
# Use NLP-based matches only for edge cases where regex fails.
# Normalize and Standardize:

# 4
# Convert numeric strings to floats.
# Standardize units (e.g., grams for weight, karats for purity).
# Write to Database:

# 5
# Update the total_carat_weight and metal_purity columns in the database.


# ---------------------------------------------------------------------------------------------------------

# Normalizes weight to grams.
def normalize_weight(weight_str):
    weight_str = weight_str.lower()
    if "oz" in weight_str:
        return float(weight_str.split()[0]) * 28.3495  # Convert ounces to grams
    elif "grams" in weight_str or "g" in weight_str:
        return float(weight_str.split()[0])
    return None

# Normalizes purity to karats.
def normalize_purity(purity_str):
    purity_str = purity_str.lower()
    if "k" in purity_str or "karat" in purity_str:
        return int(purity_str.split()[0])
    return None

def extract_from_item_specifics(row):
    """
    Extracts weight and purity from item_specifics if available.

    Args:
        row (tuple): A tuple containing item details.

    Returns:
        dict: A dictionary with normalized weight and purity, or None if not found.
    """

    total_carat_weight = row[4]
    metal_purity = row[5]

    if not total_carat_weight and not metal_purity:
        return None

    # Normalize weight
    if total_carat_weight:
        weight = normalize_weight(total_carat_weight)

    # Normalize purity
    if metal_purity:
        purity = normalize_purity(metal_purity)

    return {"weight": weight, "purity": purity}

def extract_metadata(conn):
    # 1
        # Prioritize structured data from item_specifics (e.g., "Total Carat Weight", "Metal Purity", "Metal").
        # Normalize values (e.g., strip units like "carats" or "grams", convert to floats).
        # Fallback to Unstructured Data:

    cursor = conn.cursor()
    query = "SELECT item_id, title, description, metal, total_carat_weight, metal_purity FROM ebay_listings;"
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        item_specifics_data = extract_from_item_specifics(row)
        if len(item_specifics_data.values()) == 2: # Check if both weight and purity are present
            # Update the 'gold' column for the current row
            update_query = """
                UPDATE ebay_listings
                SET total_carat_weight = %s, metal_purity = %s
                WHERE item_id = %s;
            """
            cursor.execute(update_query, (item_specifics_data["weight"], item_specifics_data["purity"], row[0]))

    conn.commit()
    print("Updated 'total_carat_weight' and 'metal_purity' columns for all rows in the ebay_listings table.")

