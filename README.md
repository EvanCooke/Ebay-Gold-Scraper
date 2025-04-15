# eBay Gold Scraper

Scrapes eBay gold listings and returns a CSV of the most profitable deals based on melt value.

---

## Project Workflow & Timeline

| Phase                     | Tasks                                                                 | Time Estimate | Tools                                                                 | Notes                                                                 |
|---------------------------|-----------------------------------------------------------------------|---------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|
| **1. Scraping Listings**  | - Learn eBay API basics.<br>- Fetch listings (titles, descriptions, prices, seller metrics).<br>- Filter by category (e.g., Bullion). | 1-2 days       | - eBay API (`ebay-sdk-python`)<br>- Python (`requests`, `pandas`)      | Start with 100-200 listings for testing. Avoid scraping; use the API to stay compliant. | eBay Buy Browse API |
| **2. Product Verification** | - Use zero-shot classifier to flag non-gold listings.<br>- Add regex rules for terms like "plated" or "hollow".<br>- Filter out non-gold items. | 2-3 days       | - Hugging Face `zero-shot-classification`<br>- Regex in Python        | Test with 20-30 labeled examples first. Refine rules iteratively.     |
| **3. Metadata Extraction** | - Set up spaCy rule-based patterns for weight/purity.<br>- Add unit standardization (e.g., convert grams to ounces).<br>- Validate extracted data. | 3-5 days       | - spaCy (EntityRuler)<br>- Python (unit conversion logic)             | Start with simple regex (e.g., `r"\d+ oz"`). Prioritize titles over descriptions. |
| **4. Scam Detection**     | - Use GPT-4 API to rate scam risk per listing.<br>- Add rule-based checks (price too low, seller rating < 90%). | 2-3 days       | - OpenAI API (`openai`)<br>- Python (`pandas`, `numpy`)               | Use a prompt like: *"Rate scam risk 1-5. Consider urgency, payment methods, and seller history."* |
| **5. Deal Valuation**     | - Fetch live gold price via API.<br>- Calculate price per ounce (adjusted for purity).<br>- Flag deals >10% below market. | 1-2 days       | - MetalPriceAPI (free tier)<br>- Python (`requests`, `pandas`)        | Cache prices to avoid hitting API rate limits.                       |
| **6. Output CSV**         | - Combine filtered data into a CSV.<br>- Exclude listings missing weight/purity or flagged as scams. | 1 day          | - Python (`pandas`, `csv`)                                           | Include columns: *Title, Weight, Purity, Price, Scam Score, Deal Score*. |
| **7. Pipeline Orchestration** | - Chain all steps into a Python script.<br>- Schedule daily runs (cron job). | 1-2 days       | - Python scripts<br>- Cron (or Task Scheduler)                       | Skip Prefect/Airflow for now. Use logging to track errors.           |
| **8. Testing & Refinement** | - Manually validate 10% of listings.<br>- Fix edge cases (e.g., misclassified purity). | 3-5 days       | - Spreadsheet (manual checks)<br>- Python (debugging)                | Iterate on regex patterns and GPT prompts.                           |

---

## Timeline Visualization
Week 1: Scraping + Product Verification
Day 1-2: eBay API setup and data collection.
Day 3-4: Zero-shot classifier + regex rules.

Week 2: Metadata Extraction + Scam Detection
Day 5-7: spaCy rules for weight/purity.
Day 8-9: GPT-4 scam detection integration.

Week 3: Deal Valuation + CSV Output
Day 10: MetalPriceAPI integration.
Day 11: CSV export and filtering.

Week 4: Pipeline Orchestration + Testing
Day 12-13: Script chaining + cron jobs.
Day 14-15: Manual validation + edge cases.


---

## Tools & Libraries

1. **Scraping/Data**:
   - `ebay-sdk-python`: Official eBay API client.
   - `pandas`: Clean and filter data.
2. **ML/NLP**:
   - `transformers` (Hugging Face): Zero-shot classification.
   - `spaCy`: Rule-based entity extraction.
   - `openai`: GPT-4 API for scam detection.
3. **APIs**:
   - **MetalPriceAPI**: Free tier for live gold prices.
4. **Orchestration**:
   - Python scripts + cron jobs (no Airflow/Prefect).
5. **Validation**:
   - Google Sheets/Excel: Manual spot-checking.

---

## Key Considerations

1. **Start Small**:
   - Begin with 100 listings to test the workflow.
   - Gradually scale to 1,000+ after debugging.
2. **Leverage GPT-4**:
   - Use it for scam detection instead of training custom models (saves 2-3 weeks).
   - Example prompt:
     ```python
     prompt = f"""
     Analyze this eBay listing for scam risk (1-5). Consider:
     - Urgency (e.g., 'RARE!', 'SELLING FAST').
     - Mismatched title/description.
     - Unusual payment methods (e.g., CashApp only).
     Listing: {title} - {description}
     Seller Rating: {seller_rating}/5
     """
     ```
3. **Manual Validation**:
   - Manually label 50-100 listings to test accuracy of GPT-4 and regex rules.
4. **Costs**:
   - eBay API: Free for 5,000 calls/month.
   - GPT-4: ~$20-$50 for 1,000 listings (cheaper with GPT-3.5-turbo).
   - MetalPriceAPI: Free for 1,000 requests/month.

---

## Risks & Mitigations

- **Risk**: GPT-4 mislabels scams.  
  **Fix**: Add rule-based checks (e.g., seller rating < 90% → auto-flag).
- **Risk**: Missing weight/purity data.  
  **Fix**: Exclude listings without both fields.
- **Risk**: eBay API rate limits.  
  **Fix**: Use batch processing and caching.

---

## Final Deliverables

1. **Python Scripts**:
   - Scraping, verification, extraction, valuation.
2. **Output CSV**:
   - Clean spreadsheet with filtered, validated deals.
3. **Documentation**:
   - A `README.md` explaining setup and dependencies.

---

## Realistic Expectations

- **MVP**: A functional script that processes 100 listings in <10 mins, with ~80% accuracy.
- **Refinement**: After 2-3 iterations, aim for 90%+ accuracy on verified gold listings.