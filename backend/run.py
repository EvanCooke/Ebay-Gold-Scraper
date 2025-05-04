# move all mains in database.py, ebay_search.py, etc. to this file
# add timers for everything and good ui in the command line

# - clear database tables
# - search ebay using api and insert into database
# - use zero shot classifier to classify each listing
# - extract weight and purity metadata from each losting where is_gold == True
# - chatGPT scam detection for scam risk score
# - find profitability of each gold listing with gold price api
# - insert new data into processed_listings table
#               - do I eben need two tables, and why? reconsider database schema