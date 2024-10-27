import pandas as pd
import aiohttp
import asyncio
import time

# Function to split DataFrame into smaller chunks
def split_dataframe(df, chunk_size=4):
    """Yield successive chunks of the DataFrame with a specified number of rows."""
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]

# Async function to query GPT API
async def query_chatgpt(session, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-oLEhZ6go57Fc39ghERvYGnNriWQ1lBTFIVnYG3Q1JlT3BlbkFJtWSsfo2DPam1twK0C4RQ12HjXPemY1cPMC2mRrQBMA",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500  # Adjust as needed
    }

    async with session.post(url, headers=headers, json=json_data) as response:
        if response.status != 200:
            print(f"Request failed: {response.status}")
            return None
        result = await response.json()
        return result['choices'][0]['message']['content']

# Function to create a prompt from a DataFrame chunk
def create_prompt(chunk):
    # Convert DataFrame chunk to CSV string with '¬' as delimiter
    chunk_string = chunk.to_csv(index=False, sep='¬', quotechar='"').strip()

    prompt = (
        f"Assess the profitability of these eBay items."
        "The eBay items are provided in the following format:\n"
        "Title¬Price¬Link¬Description\n"
        "Return the result in CSV format like this:\n"
        "Title, Link, Price, Melt Value, Profit, Assessment\n"
        "The spot price of solid gold is $87.95 per gram.\n"
        """    Instructions:
        1. Extract the karat (e.g., 10K, 14K) and weight (in grams) from the title or description.
        2. If the item is not solid gold (e.g., if it is plated, filled, or gold-tone), do not include it in your response.
        3. If the item is solid gold, calculate the melt value based on the following spot price: $87.95 per gram of 24K gold.
        4. For lower-karat gold, adjust accordingly:
        - 10K = 41.7% pure
        - 14K = 58.5% pure
        - 18K = 75% pure
        5. If the melt value is higher than the listing price, put "Good Deal" for assessment. If not, put "Not Profitable" for assessment.
        6. If information is missing (like weight or karat), do not include it in your response.

        Now, here are the eBay items:\n\n{chunk_string}
    """
    )
    return prompt

# Main async function to process all chunks
async def process_chunks(chunks):
    async with aiohttp.ClientSession() as session:
        tasks = []  # List to store all query tasks
        for i, chunk in enumerate(chunks):
            prompt = create_prompt(chunk)
            print(f"Submitting query for chunk {i + 1}/{len(chunks)}...")
            task = asyncio.ensure_future(query_chatgpt(session, prompt))
            tasks.append(task)

        # Wait for all tasks to complete
        responses = await asyncio.gather(*tasks)
        return responses

# Load the CSV data
df = pd.read_csv('results.csv')

# Split the DataFrame into chunks of 10 entries each
chunks = list(split_dataframe(df, chunk_size=10))

# Run the async event loop to process the chunks
start_time = time.time()
responses = asyncio.run(process_chunks(chunks))
end_time = time.time()

# Filter out None responses (in case of failed requests)
valid_responses = [resp for resp in responses if resp]

# Combine all responses into a single CSV-compatible string
final_csv_content = "\n".join(valid_responses)

# Save the final output to a CSV file
with open('profitable_items.csv', 'w') as f:
    f.write(final_csv_content)

print(f"All assessments saved to 'profitable_items.csv'.")
print(f"Time taken: {end_time - start_time:.2f} seconds")
