import pandas as pd
import aiohttp
import asyncio
import time
from io import StringIO
import os
from dotenv import load_dotenv
import backoff

# Load environment variables
load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

# Gold prices per gram for different karats
GOLD_PRICES = {
    24: 65.37,
    22: 59.92,
    18: 49.03,
    14: 38.13,
    10: 27.24,
}

CSV_DELIMITER = '¬'

def split_dataframe(df, chunk_size=4):
    """Split DataFrame into chunks for processing."""
    return [df.iloc[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

@backoff.on_exception(
    backoff.expo,
    (aiohttp.ClientError, asyncio.TimeoutError),
    max_tries=3
)
async def query_chatgpt(session, prompt, retry_count=0):
    """Query ChatGPT API with exponential backoff retry."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.3  # Lower temperature for more consistent outputs
    }
    
    try:
        async with session.post(url, headers=headers, json=json_data, timeout=30) as response:
            if response.status == 429:  # Rate limit exceeded
                if retry_count < 3:
                    wait_time = (2 ** retry_count) * 5
                    await asyncio.sleep(wait_time)
                    return await query_chatgpt(session, prompt, retry_count + 1)
                return None
            
            if response.status != 200:
                print(f"Request failed with status {response.status}")
                return None
                
            result = await response.json()
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error in API request: {e}")
        return None

def create_prompt(chunk):
    """Create a detailed prompt for GPT analysis."""
    chunk_string = chunk.to_csv(sep=CSV_DELIMITER, index=False)
    return f"""Analyze these eBay gold items and extract karat and weight information.
Input data (CSV with '{CSV_DELIMITER}' delimiter):

Title{CSV_DELIMITER}Price{CSV_DELIMITER}Link{CSV_DELIMITER}Description
{chunk_string}

Return only CSV data with these exact columns, separated by '{CSV_DELIMITER}':
Title{CSV_DELIMITER}Link{CSV_DELIMITER}Price{CSV_DELIMITER}Karat{CSV_DELIMITER}Weight

Rules:
1. Only include items with clearly stated karat (K) and weight (grams)
2. Exclude non-solid gold items (plated, filled, tone)
3. Exclude non-meltable items (molds, testing kits)
4. Extract exact numbers only
5. Return pure CSV format with no additional text

Example output:
14K Gold Ring{CSV_DELIMITER}https://example.com{CSV_DELIMITER}$199.99{CSV_DELIMITER}14K{CSV_DELIMITER}4.5"""

async def process_chunks(chunks):
    """Process chunks with rate limiting."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, chunk in enumerate(chunks):
            prompt = create_prompt(chunk)
            print(f"Processing chunk {i + 1}/{len(chunks)}...")
            # Add delay between chunks to avoid rate limits
            if i > 0:
                await asyncio.sleep(1)
            task = asyncio.ensure_future(query_chatgpt(session, prompt))
            tasks.append(task)
        return await asyncio.gather(*tasks)

def parse_csv_response(response_text):
    """Parse GPT response into DataFrame with error handling."""
    if not response_text or not isinstance(response_text, str):
        return None
    
    try:
        # Clean response and parse CSV
        cleaned_text = response_text.strip()
        df = pd.read_csv(
            StringIO(cleaned_text),
            sep=CSV_DELIMITER,
            header=None,
            names=['Title', 'Link', 'Price', 'Karat', 'Weight'],
            skip_blank_lines=True
        )
        
        # Clean and validate data
        df['Price'] = df['Price'].str.extract(r'(\d+\.?\d*)').astype(float)
        df['Karat'] = df['Karat'].str.extract(r'(\d+)').astype(int)
        df['Weight'] = df['Weight'].astype(float)
        
        return df[df['Karat'].notna() & df['Weight'].notna()]
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

def calculate_melt_value(row):
    """Calculate melt value with validation."""
    try:
        karat = int(row['Karat'])
        weight = float(row['Weight'])
        
        if karat in GOLD_PRICES and weight > 0:
            return GOLD_PRICES[karat] * weight
        return 0
    except (ValueError, TypeError):
        return 0

def analyze_results(df):
    """Generate analysis summary."""
    profitable_items = len(df[df['Profit'] > 0])
    total_potential_profit = df[df['Profit'] > 0]['Profit'].sum()
    
    return {
        'total_items': len(df),
        'profitable_items': profitable_items,
        'total_profit': total_potential_profit,
        'avg_profit_margin': (df[df['Profit'] > 0]['Profit'] / df[df['Profit'] > 0]['Price']).mean() * 100
    }

async def main():
    try:
        # Load input data
        print("Loading data...")
        df = pd.read_csv('search-results.csv', sep=CSV_DELIMITER, engine='python')
        
        # Process in chunks
        chunks = split_dataframe(df, chunk_size=5)
        print(f"Processing {len(chunks)} chunks...")
        
        start_time = time.time()
        responses = await process_chunks(chunks)
        
        # Combine and process results
        all_data = []
        for response in responses:
            if response:
                parsed_df = parse_csv_response(response)
                if parsed_df is not None and not parsed_df.empty:
                    all_data.append(parsed_df)
        
        if not all_data:
            print("No valid data processed")
            return
        
        # Create final analysis
        final_df = pd.concat(all_data, ignore_index=True)
        final_df['Melt_Value'] = final_df.apply(calculate_melt_value, axis=1)
        final_df['Profit'] = final_df['Melt_Value'] - final_df['Price']
        final_df['Assessment'] = final_df['Profit'].apply(
            lambda x: 'Profitable' if x > 0 else 'Not Profitable'
        )
        
        # Round numerical columns
        for col in ['Price', 'Melt_Value', 'Profit']:
            final_df[col] = final_df[col].round(2)
        
        # Save results
        output_file = 'gold_analysis_results.csv'
        final_df.to_csv(output_file, sep=CSV_DELIMITER, index=False)
        
        # Print analysis
        analysis = analyze_results(final_df)
        print("\nAnalysis Complete!")
        print(f"Total items analyzed: {analysis['total_items']}")
        print(f"Profitable items found: {analysis['profitable_items']}")
        print(f"Total potential profit: ${analysis['total_profit']:.2f}")
        print(f"Average profit margin: {analysis['avg_profit_margin']:.1f}%")
        print(f"Results saved to: {output_file}")
        
        print(f"\nProcessing time: {time.time() - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error in main process: {e}")

if __name__ == "__main__":
    asyncio.run(main())