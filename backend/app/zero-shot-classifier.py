from transformers import pipeline

# Load the zero-shot classification pipeline
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define regex for non-gold terms
non_gold_terms = r"(plated|hollow|gold-tone|filled|overlay)"

def classify_listing(listing):

    # Extract title and description from the row
    title = listing.get("title", "")
    description = listing.get("description", "")

    # Combine title and description for classification
    text = title + " " + description
    candidate_labels = ["gold", "non-gold"]

    # Perform zero-shot classification
    result = classifier(text, candidate_labels)
    return result["labels"][0]  # Return the label with the highest confidence

# Example usage
title = "Beautiful gold-plated necklace"
description = "This necklace is gold-plated and not solid gold."
print(classify_listing(title, description))  # Output: "non-gold"

if __name__ == "__main__":
    pass