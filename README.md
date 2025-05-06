# eBay Gold Profits Scraper
Ingests eBay gold listings, filters genuine gold items, extracts metadata, computes melt
value, assesses scam risk, and presents profitable, affiliate-linked deals.
---

## Project Workflow & Timeline

| Phase                      | Tasks                                                                                                              | Tools & Notes                                                                    |
|----------------------------|--------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **1. Scraping Listings**   | - Configure eBay API credentials.<br>- Fetch listings (title, description, price, seller metrics, URLs).<br>- Filter by category and `conditionId`. | • eBay Browse API + `requests`<br>• Python (`pandas`)                            |
| **2. Product Verification**| - Apply regex rules for “plated”/“hollow”.<br>- Zero-shot classification (gold vs. non-gold) for edge cases.      | • Python `re`<br>• HF Transformers zero-shot classifier                           |
| **3. Metadata Extraction** | - Prefer structured `item_specifics` JSON for “Total Carat Weight” & “Metal Purity”.<br>- Fallback to hybrid regex + spaCy (EntityRuler/Matcher) over `title` + `description`.<br>- Normalize units (grams, karats). | • spaCy (EntityRuler & Matcher)<br>• Python unit-conversion logic                 |
| **4. Scam Detection**      | - Rule-based checks (price far below melt, seller rating < 90%, new accounts).<br>- GPT-4 (or 3.5) risk-score prompt. | • OpenAI API<br>• Python (`pandas`, `numpy`)                                      |
| **5. Deal Valuation**      | - Fetch live spot gold price.<br>- Calculate effective price (unit × purity).<br>- Flag > 10% below market.         | • MetalPriceAPI<br>• Python (`requests`, `pandas`), cache results                |
| **6. Database Integration**| - Upsert into PostgreSQL.<br>- Skip listings missing weight/purity or flagged as scams (conditional UPDATE).       | • `psycopg2`                                                                     |
| **7. Pipeline Orchestration**| - Chain modules into one script.<br>- Schedule daily via cron.<br>- Log errors, missing extractions, confidence. | • Python scripts<br>• Cron job (or Task Scheduler)                               |
| **8. Testing & Refinement**| - Manual spot-check 10–20% of listings.<br>- Refine regex/spaCy patterns and LLM prompts.                         | • Google Sheets/Excel<br>• Python debugging & unit tests                         |

---
## Key Attributes & Extraction Targets

| Column               | Source                          | Extraction Method                                                                 |
|----------------------|----------------------------------|----------------------------------------------------------------------------------|
| `item_id`, `title`, …| API fields                      | Stored directly; not parsed                                                     |
| **`item_specifics`** | Browse API (structured JSON)    | Primary source for `total_carat_weight` & `metal_purity`                        |
| **`title` + `description`** | Fallback text           | Regex & spaCy for weight (`\d+(?:\.\d+)?\s*(g|oz)\b`) and purity (`\d{1,2}\s*(k|kt|karat)`) |
| `price`, `currency`  | API fields                      | Used for melt comparison and currency conversion                                |
| `seller_*`, `shipping_*` | API fields                  | Features for scam risk and filtering                                            |
| `gold` (BOOLEAN)     | Classifier output               | Zero-shot or fine-tuned model                                                   |
| `scam_score`         | LLM + rules                    | 1–5 scale                                                                       |
---
## Quickstart
1. **Clone & install**
 ```bash
 git clone <repo-url>
 cd ebay-gold-scraper
 pip install -r requirements.txt
 ```
2. **Configure**
 Create a `.env` file with:
 ```
 CLIENT_ID=
 CLIENT_SECRET=
 DB_NAME=
 DB_USER=
 DB_PASSWORD=
 DB_HOST=
 DB_PORT=
 FLASK_APP=
 FLASK_ENV=
 SECRET_KEY=
 VERIFICATION_TOKEN=
 ENDPOINT_URL=
 ```
3. **Run modules**
 ```bash
 python ebay_search.py # Step 1: fetch listings
 python zero_shot_classifier.py # Step 2: filter non-gold
 python extract_metadata.py # Step 3: weight & purity extraction
 python scam_risk_score.py # Step 4: scam detection & valuation
 python database.py # Step 6: upsert into PostgreSQL
 ```
4. **Schedule daily**
 ```bash
 # crontab -e
 0 2 * * * /usr/bin/python /path/to/pipeline.py >> /var/log/gold-scraper.log 2>&1
 ```
5. **Monitor & refine**
 - Check logs for missing extractions.
 - Update regex/spaCy patterns and LLM prompts as needed.
---
## Tech Stack
- **Language & DB**: Python 3.x, PostgreSQL
- **Data & HTTP**: `requests`, `pandas`, `json`
- **NLP & ML**: `re`, spaCy, Hugging Face Transformers, OpenAI API
- **APIs**: eBay Browse API, MetalPriceAPI
- **Deployment**: AWS RDS, S3 (for static assets), Cron jobs
---
## Goals & Metrics
- **MVP**: Process 100 listings in < 10 min, ≥ 80% accurate weight/purity extraction.
- **Iteration**: Reach ≥ 90% extraction accuracy and reliable scam scoring after 2–3
cycles.
---
