# eBay Gold Scraper

Scrapes eBay gold listings and uploads the data directly to a PostgreSQL database. The project identifies profitable deals based on gold melt value while filtering out scams and non-gold items.

---

## Project Workflow & Timeline

| Phase                     | Tasks                                                                 | Time Estimate | Tools                                                                 | Notes                                                                 |
|---------------------------|-----------------------------------------------------------------------|---------------|-----------------------------------------------------------------------|-----------------------------------------------------------------------|
| **1. Scraping Listings**  | - Learn eBay API basics.<br>- Fetch listings (titles, descriptions, prices, seller metrics).<br>- Filter by category (e.g., Bullion). | Completed       | - eBay API (`requests` for API calls + `ebay-oauth-python-client` for authentication)<br>- Python (`requests`, `pandas`)      | Start with 100-200 listings for testing. Avoid scraping; use the API to stay compliant. |
| **2. Product Verification** | - Use regex rules for terms like "plated" or "hollow".<br>- Filter out non-gold items.<br>- Optionally use a zero-shot classifier for edge cases. | 2-3 days       | - Regex in Python<br>- Hugging Face `zero-shot-classification` (optional)        | Test with 20-30 labeled examples first. Refine rules iteratively.     |
| **3. Metadata Extraction** | - Extract weight and purity using regex and spaCy.<br>- Add unit standardization (e.g., convert grams to ounces).<br>- Validate extracted data. | 3-5 days       | - spaCy (EntityRuler)<br>- Python (unit conversion logic)             | Start with simple regex (e.g., `r"\d+ oz"`). Prioritize titles over descriptions. |
| **4. Scam Detection**     | - Use GPT-4 API to rate scam risk per listing.<br>- Add rule-based checks (price too low, seller rating < 90%). | 2-3 days       | - OpenAI API (`openai`)<br>- Python (`pandas`, `numpy`)               | Use a prompt like: *"Rate scam risk 1-5. Consider urgency, payment methods, and seller history."* |
| **5. Deal Valuation**     | - Fetch live gold price via API.<br>- Calculate price per ounce (adjusted for purity).<br>- Flag deals >10% below market. | 1-2 days       | - MetalPriceAPI (free tier)<br>- Python (`requests`, `pandas`)        | Cache prices to avoid hitting API rate limits.                       |
| **6. Database Integration** | - Upload filtered data directly to PostgreSQL.<br>- Exclude listings missing weight/purity or flagged as scams. | 1 day          | - Python (`psycopg2`)                                                | Replace CSV output with direct database integration.                 |
| **7. Pipeline Orchestration** | - Chain all steps into a Python script.<br>- Schedule daily runs (cron job). | 1-2 days       | - Python scripts<br>- Cron (or Task Scheduler)                       | Skip Prefect/Airflow for now. Use logging to track errors.           |
| **8. Testing & Refinement** | - Manually validate 10% of listings.<br>- Fix edge cases (e.g., misclassified purity). | 3-5 days       | - Spreadsheet (manual checks)<br>- Python (debugging)                | Iterate on regex patterns and GPT prompts.                           |

---

## Timeline Visualization

### Week 1: Scraping + Product Verification
- **Day 1-2**: eBay API setup and data collection.
- **Day 3-4**: Regex rules for filtering non-gold items.

### Week 2: Metadata Extraction + Scam Detection
- **Day 5-7**: Regex and spaCy rules for weight/purity extraction.
- **Day 8-9**: GPT-4 scam detection integration.

### Week 3: Deal Valuation + Database Integration
- **Day 10**: MetalPriceAPI integration for live gold prices.
- **Day 11**: Upload filtered data directly to PostgreSQL.

### Week 4: Pipeline Orchestration + Testing
- **Day 12-13**: Script chaining and cron job setup.
- **Day 14-15**: Manual validation and edge case fixes.

---

## Tools & Libraries

1. **Scraping/Data**:
   - `requests`: For eBay API calls.
   - `pandas`: For data cleaning and filtering.
2. **ML/NLP**:
   - `regex`: For filtering non-gold items.
   - `spaCy`: For rule-based entity extraction (weight, purity).
   - `openai`: For GPT-4 scam detection.
3. **APIs**:
   - **eBay API**: For fetching listings and item details.
   - **MetalPriceAPI**: For live gold prices.
4. **Database**:
   - `psycopg2`: For PostgreSQL integration.
5. **Orchestration**:
   - Python scripts + cron jobs (no Airflow/Prefect).
6. **Validation**:
   - Google Sheets/Excel: For manual spot-checking.

---

## Key Considerations

1. **Database Integration**:
   - Replace CSV output with direct database uploads for scalability.
   - Ensure the database schema supports all required fields (e.g., weight, purity, scam score).

2. **Start Small**:
   - Begin with 100 listings to test the workflow.
   - Gradually scale to 1,000+ after debugging.

3. **Leverage GPT-4**:
   - Use GPT-4 for scam detection first for MVP before training custom models.

4. **Manual Validation**:
   - Manually label 50-100 listings to test the accuracy of regex rules and GPT-4.

5. **Costs**:
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
   - Scraping, verification, extraction, valuation, and database integration.
2. **Database**:
   - PostgreSQL database with filtered, validated listings.
3. **Documentation**:
   - A `README.md` explaining setup, dependencies, and usage.

---

## Realistic Expectations

- **MVP**: A functional script that processes 100 listings in <10 mins, with ~80% accuracy.
- **Refinement**: After 2-3 iterations, aim for 90%+ accuracy on verified gold listings.