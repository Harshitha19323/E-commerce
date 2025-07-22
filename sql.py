import sqlite3
import csv
import os
import requests

# Define the database file name
DATABASE_FILE = "product_data.db"

# Define the Google Sheets URLs for the CSV exports
ELIGIBILITY_URL = "https://docs.google.com/spreadsheets/d/1Loc32KsHwEGhLAahSfMA6t1aZdEvxJIPADxpdzZEZTw/export?format=csv&gid=95626969"
TOTAL_SALES_URL = "https://docs.google.com/spreadsheets/d/1ftXt9Z6uEXUMlIHSZK0CR2kLlNZyj8TUi4lQmMF6qWo/export?format=csv&gid=1942712772"
AD_SALES_URL = "https://docs.google.com/spreadsheets/d/1ZATJteA4sU7DXN-fqJxG8Td_Nwif5QB2fTQvGK8LegY/export?format=csv&gid=1720576947"

# Define local file names for the downloaded CSVs
ELIGIBILITY_CSV_LOCAL = "product_eligibility.csv"
TOTAL_SALES_CSV_LOCAL = "product_total_sales.csv"
AD_SALES_CSV_LOCAL = "product_ad_sales.csv"

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables(connection):
    """
    Creates the necessary tables in the database if they don't already exist.
    """
    cursor = connection.cursor()

    # Table for Product-Level Eligibility
    eligibility_table_info = """
    CREATE TABLE IF NOT EXISTS product_eligibility (
        eligibility_datetime_utc TEXT,
        item_id INTEGER,
        eligibility BOOLEAN, -- SQLite uses 0 for FALSE, 1 for TRUE
        message TEXT
    );
    """
    cursor.execute(eligibility_table_info)

    # Table for Product-Level Total Sales
    total_sales_table_info = """
    CREATE TABLE IF NOT EXISTS product_total_sales (
        date TEXT,
        item_id INTEGER,
        total_sales REAL,
        total_units_ordered INTEGER
    );
    """
    cursor.execute(total_sales_table_info)

    # Table for Product-Level Ad Sales
    ad_sales_table_info = """
    CREATE TABLE IF NOT EXISTS product_ad_sales (
        date TEXT,
        item_id INTEGER,
        ad_sales REAL,
        impressions INTEGER,
        ad_spend REAL,
        clicks INTEGER,
        units_sold INTEGER
    );
    """
    cursor.execute(ad_sales_table_info)

    connection.commit()

def download_csv_from_url(url: str, local_file_path: str) -> bool:
    """
    Downloads a CSV file from a given URL and saves it locally.
    Returns True on success, False on failure.
    """
    if not url.startswith(('http://', 'https://')):
        print(f"Error: Provided URL '{url}' is not a valid HTTP/HTTPS URL. Please ensure it starts with 'http://' or 'https://'.")
        return False

    print(f"Attempting to download from {url} to {local_file_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        with open(local_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {local_file_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False
    except IOError as e:
        print(f"Error writing to local file {local_file_path}: {e}")
        return False

def import_data_from_csv(connection, csv_file_path, table_name, column_mapping):
    """
    Imports data from a CSV file into a specified SQL table.
    column_mapping is a dictionary mapping CSV header names to SQL column names.
    """
    cursor = connection.cursor()
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}. Skipping import for {table_name}.")
        return

    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Print actual fieldnames for debugging purposes
            # print(f"Actual CSV headers for {csv_file_path}: {reader.fieldnames}") # Commented out for cleaner output during normal run

            # Create a mapping from stripped actual CSV header to its original form
            stripped_fieldnames_map = {header.strip(): header for header in reader.fieldnames}

            sql_columns = []
            csv_keys_to_use = [] # These will be the exact keys from reader.fieldnames

            for expected_csv_key, sql_col in column_mapping.items():
                stripped_expected_key = expected_csv_key.strip()
                if stripped_expected_key in stripped_fieldnames_map:
                    # Use the original (unstripped) CSV key found in the file
                    original_csv_key = stripped_fieldnames_map[stripped_expected_key]
                    sql_columns.append(sql_col)
                    csv_keys_to_use.append(original_csv_key)
                # else: # Commented out warning for cleaner output during normal run
                #     print(f"Warning: Expected CSV column '{expected_csv_key}' (stripped: '{stripped_expected_key}') not found in actual headers {reader.fieldnames} for table '{table_name}'.")

            if not sql_columns:
                print(f"No valid columns found for import from '{csv_file_path}' to '{table_name}'. Skipping.")
                return

            placeholders = ', '.join(['?' for _ in sql_columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(sql_columns)}) VALUES ({placeholders});"
            
            data_to_insert = []
            for row in reader:
                mapped_row = []
                for csv_key_from_file in csv_keys_to_use: # Use the exact keys from the file
                    value = row.get(csv_key_from_file)
                    # Convert 'TRUE'/'FALSE' strings to 1/0 for BOOLEAN in SQLite
                    if value is not None and isinstance(value, str) and value.upper() == 'TRUE':
                        mapped_row.append(1)
                    elif value is not None and isinstance(value, str) and value.upper() == 'FALSE':
                        mapped_row.append(0)
                    else:
                        mapped_row.append(value)
                data_to_insert.append(tuple(mapped_row))

            if data_to_insert:
                cursor.executemany(insert_sql, data_to_insert)
                connection.commit()
                # print(f"Successfully imported {len(data_to_insert)} records into '{table_name}' from '{csv_file_path}'.") # Commented out for cleaner output during normal run
            else:
                print(f"No data found in '{csv_file_path}' to import into '{table_name}'.")

    except Exception as e:
        print(f"Error importing data from {csv_file_path} to {table_name}: {e}")

def execute_query(sql_query: str):
    """
    Executes a given SQL query and returns the results.
    This function is intended to be called by the AI Agent.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            if sql_query.strip().upper().startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    results.append(dict(row))
                return {"columns": columns, "rows": results}
            else:
                conn.commit()
                return {"message": "Query executed successfully."}
        except sqlite3.Error as e:
            return {"error": str(e)}
        finally:
            conn.close()
    return {"error": "Database connection failed."}

def initialize_database():
    """
    Initializes the database: creates tables if they don't exist.
    This function is called by the AI Agent.
    It does NOT delete the database file on every call.
    """
    conn = get_db_connection()
    if conn:
        try:
            create_tables(conn)
            # Only import data if tables are empty, or if you want to force re-import
            # For this setup, we assume data is imported via the __main__ block when sql.py is run directly.
            # If you want to ensure data is always present when agent starts, you'd add import logic here
            # but that's generally not recommended for a production agent (data should be managed separately).
        except sqlite3.Error as e:
            print(f"Error during database initialization: {e}")
            raise # Re-raise to let the agent know initialization failed
        finally:
            conn.close()


def display_sample_data(connection):
    """
    Displays a sample of data from each created table.
    This function is primarily for testing when sql.py is run directly.
    """
    cursor = connection.cursor()

    print("\n--- Sample Data from product_eligibility ---")
    data = cursor.execute("SELECT * FROM product_eligibility LIMIT 5;")
    for row in data:
        print(dict(row))

    print("\n--- Sample Data from product_total_sales ---")
    data = cursor.execute("SELECT * FROM product_total_sales LIMIT 5;")
    for row in data:
        print(dict(row))

    print("\n--- Sample Data from product_ad_sales ---")
    data = cursor.execute("SELECT * FROM product_ad_sales LIMIT 5;")
    for row in data:
        print(dict(row))

if __name__ == "__main__":
    # This block is for initial setup and testing of the database.
    # It will clear and re-populate the database every time it's run directly.
    print(f"Running {os.path.basename(__file__)} directly for initial database setup.")
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        print(f"Removed existing database file: {DATABASE_FILE}")

    # List of CSV URLs and their corresponding local file paths
    csv_files_to_download = [
        (ELIGIBILITY_URL, ELIGIBILITY_CSV_LOCAL),
        (TOTAL_SALES_URL, TOTAL_SALES_CSV_LOCAL),
        (AD_SALES_URL, AD_SALES_CSV_LOCAL)
    ]

    # Download all CSV files
    all_downloads_successful = True
    for url, local_path in csv_files_to_download:
        if not download_csv_from_url(url, local_path):
            all_downloads_successful = False
            print(f"Failed to download {url}. Cannot proceed with import for this file.")

    if not all_downloads_successful:
        print("One or more CSV files failed to download. Database import may be incomplete.")
        
    conn = get_db_connection()
    if conn:
        try:
            create_tables(conn)

            # Define column mappings from CSV headers to SQL table columns
            eligibility_cols = {
                'eligibility_datetime_utc': 'eligibility_datetime_utc',
                'item_id': 'item_id',
                'eligibility': 'eligibility',
                'message': 'message'
            }
            import_data_from_csv(conn, ELIGIBILITY_CSV_LOCAL, 'product_eligibility', eligibility_cols)

            total_sales_cols = {
                'date': 'date',
                'item_id': 'item_id',
                'total_sales': 'total_sales',
                'total_units_ordered': 'total_units_ordered'
            }
            import_data_from_csv(conn, TOTAL_SALES_CSV_LOCAL, 'product_total_sales', total_sales_cols)

            ad_sales_cols = {
                'date': 'date',
                'item_id': 'item_id',
                'ad_sales': 'ad_sales',
                'impressions': 'impressions',
                'ad_spend': 'ad_spend',
                'clicks': 'clicks',
                'units_sold': 'units_sold'
            }
            import_data_from_csv(conn, AD_SALES_CSV_LOCAL, 'product_ad_sales', ad_sales_cols)

            display_sample_data(conn)

        except sqlite3.Error as e:
            print(f"An error occurred during database operations: {e}")
        finally:
            conn.close()
            print("Database connection closed.")
            
            # Clean up downloaded CSV files
            print("\nCleaning up downloaded CSV files...")
            for _, local_path in csv_files_to_download:
                if os.path.exists(local_path):
                    os.remove(local_path)
                    print(f"Removed temporary file: {local_path}")
