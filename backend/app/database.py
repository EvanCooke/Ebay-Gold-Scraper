import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import Json  # For handling JSON data
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")  # Default to localhost if not set
DB_PORT = os.getenv("DB_PORT", "5432")  # Default to 5432 if not set

def create_database():
    """Create a new PostgreSQL database"""
    try:
        # Connect to the PostgreSQL server (not a specific database)
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )

        # Set autocommit to True for CREATE DATABASE
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        conn.autocommit = True  # Simplified autocommit
        cursor = conn.cursor()

        # Check if the database exists 
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        conn.close()

    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        if conn:
           conn.close()

def connect_to_db():
    """Connects to a PostgreSQL database and returns the connection object."""
    try:
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print(f"Connected to database '{DB_NAME}' successfully.")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables(conn):
    """Creates the tables"""
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        # Use a single transaction
        cursor.execute("BEGIN;")

        # ebay_listings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ebay_listings (
                item_id VARCHAR(255) PRIMARY KEY,
                title TEXT NOT NULL,
                price DECIMAL NOT NULL,
                currency VARCHAR(10) NOT NULL,
                seller_username VARCHAR(255) NOT NULL,
                seller_feedback_score INTEGER,
                feedback_percent DECIMAL,
                image_url TEXT,
                item_url TEXT NOT NULL,
                shipping_options JSON,
                top_rated_buying_experience BOOLEAN,
                description TEXT,
                returns_accepted BOOLEAN,
                item_specifics JSON,
                metal TEXT,
                total_carat_weight TEXT,
                metal_purity TEXT,      
                gold BOOLEAN
                weight FLOAT,
                purity INT,

            )
        """)

        # ai_processed_listings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_processed_listings (
                ebay_item_id VARCHAR(255),
                weight VARCHAR(255),
                purity VARCHAR(255),
                scrap_value DECIMAL,
                profit DECIMAL,
                scam_score INTEGER,
                deal_score DECIMAL,
                PRIMARY KEY (ebay_item_id),
                FOREIGN KEY (ebay_item_id) REFERENCES ebay_listings(item_id)
            )
        """)

        conn.commit()
        print("Tables 'ebay_listings' and 'ai_processed_listings' created successfully.")

    except psycopg2.Error as e:
        cursor.execute("ROLLBACK;")
        print(f"Error creating tables: {e}")
        print("Rolled back the transaction.")
    finally:
        cursor.close()

def insert_data(conn, table_name, data):
    """Inserts data into the specified table"""
    if conn is None:
        return
    
    cursor = conn.cursor()

    try:
        if table_name == "ebay_listings":

            # Insert data into ebay_listings
            cursor.execute("""
                INSERT INTO ebay_listings (
                    item_id, title, price, currency, seller_username, seller_feedback_score,
                    feedback_percent, image_url, item_url, shipping_options,
                    top_rated_buying_experience, description, returns_accepted, item_specifics, metal,
                    total_carat_weight, metal_purity, is_gold
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_id) DO NOTHING;
            """, (
                data['item_id'],
                data['title'],
                data['price'],
                data['currency'],
                data['seller_username'],
                data['seller_feedback_score'],
                data['feedback_percent'],
                data['image_url'],
                data['item_url'],
                Json(data['shipping_options']) if data.get('shipping_options') else None,
                data['top_rated_buying_experience'],
                data['description'],
                data['returns_accepted'],
                Json(data['item_specifics']) if data.get('item_specifics') else None,
                data['metal'],
                data.get('total_carat_weight'),  # New column for total carat weight
                data.get('metal_purity'),        # New column for metal purity
                data.get('is_gold', None)        # Optional: Include is_gold if available
            ))

        elif table_name == "ai_processed_listings":
            # Insert data into ai_processed_listings
            cursor.execute("""
                INSERT INTO ai_processed_listings (
                    ebay_item_id, weight, purity, scrap_value, profit, scam_score, deal_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ebay_item_id) DO UPDATE
                SET weight = %s, purity = %s, scrap_value = %s, profit = %s,
                    scam_score = %s, deal_score = %s;
            """, (
                data['ebay_item_id'],
                data['weight'],
                data['purity'],
                data['scrap_value'],
                data['profit'],
                data['scam_score'],
                data['deal_score'],
                # Additional values for the UPDATE clause
                data['weight'],
                data['purity'],
                data['scrap_value'],
                data['profit'],
                data['scam_score'],
                data['deal_score']
            ))

        conn.commit()  # Commit the transaction
        print("Data inserted successfully.")
        return True  # Consistent return for success

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error inserting data: {e}")
        return False  # Indicate failure to insert
    finally:
        cursor.close()
        #conn.close() # Close the connection here if you want to close after each insert
        # Otherwise, manage connection closure in the main block
        

def fetch_data(conn, query, params=None, fetchone=False):
    """
    Fetches data from the database based on the provided query.

    Args:
        conn: The database connection object.
        query: The SQL query to execute.v x
        params: Optional parameters to pass to the query (for security).
        fetchone: If True, fetch only one result; otherwise, fetch all.

    Returns:
        The fetched data (single row or list of rows), or None on error.
    """
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetchone:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        return result
    except psycopg2.Error as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        cursor.close()

def clear_tables(conn):
    """
    Clears all data from the ebay_listings and ai_processed_listings tables.

    Args:
        conn: The database connection object.
    """
    if conn is None:
        print("No database connection. Cannot clear tables.")
        return

    cursor = conn.cursor()
    try:
        # Clear data from ai_processed_listings first due to foreign key dependency
        cursor.execute("TRUNCATE TABLE ai_processed_listings RESTART IDENTITY CASCADE;")
        cursor.execute("TRUNCATE TABLE ebay_listings RESTART IDENTITY CASCADE;")
        conn.commit()
        print("Tables 'ai_processed_listings' and 'ebay_listings' cleared successfully.")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"Error clearing tables: {e}")
    finally:
        cursor.close()


if __name__ == "__main__":
    conn = connect_to_db()
    if conn:
        # create_tables(conn)

        # Example data (replace with your actual data)
        ebay_data = {
            'item_id': '12345',
            'title': '24k Gold Necklace',
            'price': 199.99,
            'currency': 'USD',
            'seller_username': 'gold_seller',
            'seller_feedback_score': 1000,
            'feedback_percent': 99.9,
            'image_url': 'http://example.com/image.jpg',
            'item_url': 'http://example.com/item/12345',
            'shipping_options': None,
            'top_rated_buying_experience': True,
            'description': 'A beautiful 24k gold necklace.',
            'returns_accepted': True,
            'item_specifics': {'Metal': 'Gold', 'Purity': '24k'},
            'metal': 'Gold',
            'total_carat_weight': '1.5',
            'metal_purity': '24k',
            'is_gold': True
        }

        ai_data = {
            'ebay_item_id': '12345abcde',  # Matching item_id
            'weight': "1 oz",
            'purity': "99.9%",
            'scrap_value': 1800.00,
            'profit': 550.00,
            'scam_score': 1,
            'deal_score': 2.5
        }

        clear_tables(conn)  # Clear tables before inserting new data

        # if insert_data(conn, "ebay_listings", ebay_data):
        #     print("ebay_listings insertion was successful")
        # else:
        #     print("ebay_listings insertion failed")

        # if insert_data(conn, "ai_processed_listings", ai_data):
        #     print("ai_processed_listings insertion was successful")
        # else:
        #     print("ai_processed_listings insertion failed")

        # # Example: Fetch all data from ebay_listings
        # query = "SELECT * FROM ebay_listings;"
        # results = fetch_data(conn, query)
        # if results:
        #     print("All ebay_listings:")
        #     for row in results:
        #         print(row)

        # # Example: Fetch a single listing by item_id
        # query = "SELECT title, price FROM ebay_listings WHERE item_id = %s;"
        # result = fetch_data(conn, query, (ebay_data['item_id'],), fetchone=True)
        # if result:
        #     print(f"\nListing with item_id '{ebay_data['item_id']}': {result}")

        conn.close()
    else:
        print("Failed to connect to the database")