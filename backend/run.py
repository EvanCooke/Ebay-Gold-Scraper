import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Import all the modules you need
from app.database import connect_to_db, create_database, create_tables, clear_tables
from app.ebay_search import (
    get_access_token, search_ebay_listings, get_item_details,
    CLIENT_ID, CLIENT_SECRET, TOKEN_URL, SEARCH_KEYWORDS, 
    MARKETPLACE_ID, RESULTS_PER_PAGE, MAX_PAGES, SELLER_FEEDBACK_MIN
)
from app.database import insert_data
from app.zero_shot_classifier import update_gold_column
from app.extract_metadata import extract_metadata
from app.calculate_profit import update_profit_column
from app.scam_risk_score import update_scam_risk_score_column

load_dotenv()

def log_step(step_name, start_time=None):
    """Helper function to log each step with timing"""
    current_time = datetime.now()
    if start_time:
        duration = current_time - start_time
        print(f"✅ {step_name} completed in {duration.total_seconds():.2f} seconds")
    else:
        print(f"🔄 Starting {step_name}...")
    return current_time

def main():
    """Main pipeline function that orchestrates the entire process"""
    pipeline_start = datetime.now()
    print(f"🚀 Starting eBay Gold Scraper Pipeline at {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Define multiple search keywords
    SEARCH_KEYWORDS_LIST = [
        'scrap gold 14k',
        'scrap gold 10k', 
        'scrap gold 18k',
        'gold jewelry scrap',
        'broken gold jewelry',
        'gold estate jewelry'
    ]
    
    # Step 1: Database Setup
    step_start = log_step("Database connection and setup")
    try:
        create_database()  # Create database if it doesn't exist
        conn = connect_to_db()
        if not conn:
            raise Exception("Failed to connect to database")
        
        # create_tables(conn)  # Ensure tables exist
        clear_tables(conn)   # Clear existing data
        log_step("Database setup", step_start)
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

    # Step 2: eBay API Authentication
    step_start = log_step("eBay API authentication")
    try:
        access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
        if not access_token:
            raise Exception("Failed to get access token")
        log_step("eBay API authentication", step_start)
    except Exception as e:
        print(f"❌ eBay API authentication failed: {e}")
        conn.close()
        return False

    # Step 3: Scrape eBay Listings
    step_start = log_step("eBay listings scraping")
    try:
        # Construct search filters
        search_filters = []
        if SELLER_FEEDBACK_MIN > 0:
            search_filters.append(f"feedbackScoreMin:[{SELLER_FEEDBACK_MIN}]")
        filter_string = ",".join(search_filters) if search_filters else None

        all_item_data = []
        max_items_per_keyword = 20  # Limit per keyword

        for keyword_index, search_keyword in enumerate(SEARCH_KEYWORDS_LIST):
            print(f"\n  🔍 Keyword {keyword_index + 1}/{len(SEARCH_KEYWORDS_LIST)}: '{search_keyword}'")
            
            page_number = 1
            items_for_this_keyword = 0
            
            while page_number <= MAX_PAGES and items_for_this_keyword < max_items_per_keyword:
                print(f"    📄 Processing page {page_number} for '{search_keyword}'...")
                
                # Calculate offset for pagination
                offset = (page_number - 1) * RESULTS_PER_PAGE

                item_summaries, total_listings = search_ebay_listings(
                    access_token=access_token,
                    search_query=search_keyword,
                    category_ids=None,
                    limit=RESULTS_PER_PAGE,
                    marketplace_id=MARKETPLACE_ID,
                    filter_str=filter_string,
                    offset=offset  # Pass the calculated offset
                )

                if total_listings == 0 or not item_summaries:
                    print(f"    ℹ️ No more listings found for '{search_keyword}'")
                    break

                for summary in item_summaries:
                    if items_for_this_keyword >= max_items_per_keyword:
                        break
                        
                    item_id = summary.get('itemId')
                    
                    # Skip duplicates
                    if any(item['item_id'] == item_id for item in all_item_data):
                        continue
                    
                    seller_info = summary.get('seller', {})
                    item_details = get_item_details(access_token, item_id, MARKETPLACE_ID)
                    
                    if item_details:
                        all_item_data.append({
                            'item_id': item_id,
                            'title': summary.get('title'),
                            'price': summary.get('price', {}).get('value'),
                            'currency': summary.get('price', {}).get('currency'),
                            'seller_username': seller_info.get('username'),
                            'seller_feedback_score': seller_info.get('feedbackScore'),
                            'feedback_percent': seller_info.get('feedbackPercentage'),
                            'image_url': summary.get('image', {}).get('imageUrl'),
                            'item_url': summary.get('itemWebUrl'),
                            'shipping_options': summary.get('shippingOptions', None),
                            'top_rated_buying_experience': summary.get('topRatedBuyingExperience'),
                            'description': item_details.get('description', None),
                            'returns_accepted': item_details.get('returns_accepted', None),
                            'metal': item_details.get('metal', None),
                            'total_carat_weight': item_details.get('total_carat_weight', None),
                            'metal_purity': item_details.get('metal_purity', None),
                            'item_specifics': item_details.get('item_specifics', {}),
                            'search_keyword': search_keyword  # Track source keyword
                        })
                        items_for_this_keyword += 1

                page_number += 1
            
            print(f"    ✅ Found {items_for_this_keyword} items for '{search_keyword}'")

        print(f"  📊 Total unique items scraped: {len(all_item_data)}")
        log_step("eBay listings scraping (multiple keywords)", step_start)
    except Exception as e:
        print(f"❌ eBay scraping failed: {e}")
        conn.close()
        return False

    # Step 4: Insert Raw Data
    step_start = log_step("Database insertion")
    try:
        successful_inserts = 0
        for item in all_item_data:
            if insert_data(conn, "ebay_listings", item):
                successful_inserts += 1
        
        print(f"  📊 Successfully inserted {successful_inserts}/{len(all_item_data)} items")
        log_step("Database insertion", step_start)
    except Exception as e:
        print(f"❌ Database insertion failed: {e}")
        conn.close()
        return False

    # Step 5: Gold Classification
    step_start = log_step("Gold classification (AI)")
    try:
        update_gold_column(conn)
        log_step("Gold classification", step_start)
    except Exception as e:
        print(f"❌ Gold classification failed: {e}")
        conn.close()
        return False

    # Step 6: Metadata Extraction
    step_start = log_step("Metadata extraction")
    try:
        extract_metadata(conn)
        log_step("Metadata extraction", step_start)
    except Exception as e:
        print(f"❌ Metadata extraction failed: {e}")
        conn.close()
        return False

    # Step 7: Profit Calculation
    step_start = log_step("Profit calculation")
    try:
        update_profit_column(conn)
        log_step("Profit calculation", step_start)
    except Exception as e:
        print(f"❌ Profit calculation failed: {e}")
        conn.close()
        return False

    # Step 8: Scam Risk Assessment
    step_start = log_step("Scam risk assessment (AI)")
    try:
        update_scam_risk_score_column(conn)
        log_step("Scam risk assessment", step_start)
    except Exception as e:
        print(f"❌ Scam risk assessment failed: {e}")
        conn.close()
        return False

    # Cleanup
    conn.close()
    
    # Final Summary
    pipeline_end = datetime.now()
    total_duration = pipeline_end - pipeline_start
    print("=" * 60)
    print(f"🎉 Pipeline completed successfully!")
    print(f"⏱️  Total duration: {total_duration.total_seconds():.2f} seconds")
    print(f"📊 Final stats: {len(all_item_data)} items processed")
    print(f"🕐 Finished at: {pipeline_end.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Pipeline failed. Check the logs above for details.")
        exit(1)
    else:
        print("\n✅ Pipeline completed successfully!")
        exit(0)