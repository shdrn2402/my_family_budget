import os
import sys
import csv
from datetime import datetime
import psycopg

# Add project root to sys.path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.config import Config

def get_category_id(category: str, subcategory: str, purchase_name: str) -> int | None:
    cat_lower = category.lower().strip()
    sub_lower = subcategory.lower().strip()
    name_lower = purchase_name.lower().strip()

    if cat_lower == "undefined":
        return None

    if cat_lower == "food":
        if sub_lower == "groceries":
            return 17
        elif sub_lower == "cafes and restaurants":
            return 18
        elif sub_lower == "fast food":
            return 16
        elif sub_lower == "sweets and pastries":
            return 16

    elif cat_lower == "home":
        if sub_lower == "household":
            return 23
        elif sub_lower == "housing":
            return 20
        elif sub_lower == "utilities":
            return 21

    elif cat_lower == "kids":
        return 29  # Toys & Clothes for both 'clothes' and 'other'

    elif cat_lower == "personal":
        if sub_lower == "clothes":
            return 32
        elif sub_lower == "education":
            return 28
        elif sub_lower == "health and beauty":
            return 30
        elif sub_lower == "leisure and entertainment":
            return 31
        elif sub_lower == "sport":
            return 35
        elif sub_lower == "personal expenses":
            if "alcohol" in name_lower or "beer" in name_lower:
                return 31
            elif "flowers" in name_lower:
                return 10
            elif "hair salon" in name_lower or "haircut" in name_lower:
                return 30
            elif "notary" in name_lower:
                return 38
            elif "screen protector" in name_lower or "usb cable" in name_lower:
                return 31
            else:
                return 31

    elif cat_lower == "pets":
        return 9

    elif cat_lower == "transport":
        if sub_lower == "car":
            return 24
        elif sub_lower == "transport":
            return 25

    print(f"Warning: Unknown category mapping for {category} / {subcategory}. Assigning NULL.")
    return None

def main():
    csv_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bank_statements", "legacy_cash_transactions_2023_2025.csv")
    
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found.")
        sys.exit(1)

    print("Connecting to database...")
    try:
        # Docker exposes DB on 5433, while .env might have 5432 for internal network
        db_port = os.getenv("EXTERNAL_DB_PORT", "5433")
        conninfo = f"dbname={Config.DB_NAME} user={Config.DB_USER} password={Config.DB_PASSWORD} host=127.0.0.1 port={db_port}"
        conn = psycopg.connect(conninfo)
        conn.autocommit = False
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

    cursor = conn.cursor()

    records_to_insert = []
    total_amount = 0.0
    earliest_date = None
    
    print("Parsing CSV...")
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['financing_source'].strip().lower() != 'cash':
                continue

            row_id = row['id']
            purchase_name = row['purchase_name']
            subcategory = row['purchase_subcategory']
            category = row['purchase_category']
            price_str = row['price']
            date_str = row['purchase_date']

            buyers_name = row.get('buyers_name', '')
            user_map = {
                'andrey': 1774578,
                'ekaterina': 90487336
            }
            user_id = user_map.get(buyers_name.strip().lower())

            try:
                price_val = float(price_str)
            except ValueError:
                print(f"Skipping row {row_id} due to invalid price: {price_str}")
                continue

            # Expenses are stored as negative
            amount = -abs(price_val)
            
            category_id = get_category_id(category, subcategory, purchase_name)
            
            external_id = f"legacy_cash_{row_id}"
            
            records_to_insert.append((
                4,  # account_id
                category_id,
                user_id,
                amount,
                purchase_name,
                date_str,
                external_id,
                'import_xls',
                'confirmed'
            ))

            total_amount += abs(price_val)

            try:
                # 2025-05-25 11:14:00+03
                clean_date_str = date_str.split('+')[0].strip()
                parsed_date = datetime.strptime(clean_date_str, "%Y-%m-%d %H:%M:%S")
                if earliest_date is None or parsed_date < earliest_date:
                    earliest_date = parsed_date
            except Exception:
                pass
                
    if not records_to_insert:
        print("No cash records found.")
        sys.exit(0)

    if earliest_date is None:
        earliest_date_str = min(r[5] for r in records_to_insert)
    else:
        earliest_date_str = earliest_date.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Found {len(records_to_insert)} cash records. Total amount: {total_amount:.2f}")

    records_to_insert.append((
        4,  # account_id
        39, # category_id (Cash withdrawal) IN DB
        None, # user_id
        total_amount, # amount (positive)
        'Historical Cash Balance Correction', # description
        earliest_date_str, # date
        'legacy_cash_correction', # external_id
        'import_xls',
        'confirmed'
    ))

    insert_query = """
        INSERT INTO budget.transactions 
        (account_id, category_id, user_id, amount, description, date, external_id, source_type, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_id) DO NOTHING
    """

    print("Inserting into database...")
    try:
        cursor.executemany(insert_query, records_to_insert)
        inserted_count = cursor.rowcount
        conn.commit()
        print(f"Successfully executed batch insertion. Rows affected returned by psycopg: {inserted_count}")
        
        cursor.execute("SELECT SUM(amount) FROM budget.transactions WHERE account_id = 4;")
        current_balance = cursor.fetchone()[0] or 0.0
        print(f"Current calculated balance for Shared Cash (account_id = 4): {current_balance:.2f}")

    except Exception as e:
        conn.rollback()
        print(f"Database error during insertion: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
