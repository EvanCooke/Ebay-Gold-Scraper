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

import re
import spacy

# Load spaCy's NLP model
nlp = spacy.load("en_core_web_sm")

# Normalizes weight to grams.
def normalize_weight(weight_str):
    try:
        if weight_str is None:
            return None
        weight_str = weight_str.lower()
        if "oz" in weight_str or "ounce" in weight_str:
            return float(weight_str.split()[0]) * 28.3495  # Convert ounces to grams
        elif "grams" in weight_str or "g" in weight_str:
            return float(weight_str.split()[0])
        return None
    except (ValueError, AttributeError):
        return None

# Normalizes purity to karats.
def normalize_purity(purity_str):
    try:
        if purity_str is None:
            return None
        # Remove non-numeric characters
        purity_str = ''.join(filter(str.isdigit, purity_str))
        purity_value = int(purity_str)

        # Validate purity range (gold purity should be between 1-24 karats)
        if purity_value < 1 or purity_value > 24:
            print(f"Warning: Invalid purity value {purity_value}. Skipping.")
            return None
            
        return purity_value
    except (ValueError, AttributeError):
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

    # Normalize weight
    weight = normalize_weight(total_carat_weight) if total_carat_weight else None
    
    # Normalize purity
    purity = normalize_purity(metal_purity) if metal_purity else None

    return {"weight": weight, "purity": purity}

def extract_from_text_blob(row):
    """
    Extracts weight and purity from the concatenated title and description using regex.

    Args:
        title (str): The title of the listing.
        description (str): The description of the listing.

    Returns:
        dict: A dictionary with normalized weight and purity, or None if not found.
    """

    # Regex patterns for weight and purity
    weight_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(oz|grams?|g)", re.IGNORECASE) # group(1) is the number, group(2) is the unit
    purity_pattern = re.compile(r"(\d{1,2})\s*(k|kt|karat?)", re.IGNORECASE)    

    text_blob = f"{row[1]} {row[2]}".lower()

    # Extract weight
    weight_match = weight_pattern.search(text_blob) # this works
    weight = normalize_weight(f"{weight_match.group(1)} {weight_match.group(2)}") if weight_match else None

    # Extract purity
    purity_match = purity_pattern.search(text_blob)
    purity = normalize_purity(f"{purity_match.group(1)} {purity_match.group(2)}") if purity_match else None

    return {"weight": weight, "purity": purity}

def extract_with_spacy(text):
    """
    Extracts weight and purity using spaCy's NLP model.

    Args:
        text (str): The text to process.

    Returns:
        dict: A dictionary with extracted weight and purity, or None if not found.
    """
    doc = nlp(text)
    weight = None
    purity = None

    # Look for weight and purity in the text
    for ent in doc.ents:
        if ent.label_ == "QUANTITY":  # spaCy's entity label for quantities
            if "oz" in ent.text.lower() or "gram" in ent.text.lower() or "g" in ent.text.lower():
                weight = normalize_weight(ent.text)
        elif ent.label_ == "CARDINAL":  # spaCy's entity label for numbers
            if "k" in ent.text.lower() or "karat" in ent.text.lower():
                purity = normalize_purity(ent.text)

    return {"weight": weight, "purity": purity}

def extract_metadata(conn):
    cursor = conn.cursor()
    successful_updates = 0
    failed_updates = 0
    
    try:
        # Fetch rows where metadata hasn't been extracted yet
        query = """
        SELECT item_id, title, description, metal, total_carat_weight, metal_purity
        FROM ebay_listings
        WHERE is_gold = TRUE
            AND (weight IS NULL OR purity IS NULL);
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            try:
                # Extract from item_specifics first
                item_specifics_data = extract_from_item_specifics(row)
                
                # If missing, try text blob extraction
                text_blob_data = extract_from_text_blob(row)
                
                # Combine results (prioritize item_specifics)
                weight = item_specifics_data.get("weight") or text_blob_data.get("weight")
                purity = item_specifics_data.get("purity") or text_blob_data.get("purity")

                print(f"Item {row[0]} - weight: {weight} purity: {purity}")

                # Use spaCy as a fallback if weight or purity is still missing
                if not weight or not purity:
                    spacy_data = extract_with_spacy(f"{row[1]} {row[2]}")
                    print("spacy_data: " + str(spacy_data))
                    weight = weight or normalize_weight(spacy_data.get("weight"))
                    purity = purity or normalize_purity(spacy_data.get("purity"))

                # Update the database if both weight and purity are found and valid
                if weight and purity and weight > 0 and 0 < purity <= 24:
                    update_query = """
                        UPDATE ebay_listings
                        SET weight = %s, purity = %s
                        WHERE item_id = %s;
                    """
                    cursor.execute(update_query, (weight, purity, row[0]))
                    successful_updates += 1
                else:
                    print(f"Skipped row {row[0]}: Missing or invalid weight ({weight}) or purity ({purity})")
                    failed_updates += 1
                    
            except Exception as e:
                print(f"Error processing metadata for item {row[0]}: {e}")
                failed_updates += 1
                continue  # Continue with next item

        conn.commit()
        print(f"Metadata extraction complete: {successful_updates} successful, {failed_updates} failed")
        
    except Exception as e:
        conn.rollback()
        print(f"Error in extract_metadata: {e}")
    finally:
        cursor.close()