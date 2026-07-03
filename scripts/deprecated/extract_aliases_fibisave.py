import os
import glob
import yaml
import pandas as pd
import re
import sys

# Add the project root to sys.path so we can import from bot
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from bot.services.categorizer import clean_fibi_business_name

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ALIASES_FILE = os.path.join(DATA_DIR, "aliases.yaml")
SQL_FILE = os.path.join(os.path.dirname(__file__), "seed_data.sql")

def get_categories_from_sql():
    categories = {}
    if not os.path.exists(SQL_FILE):
        return categories
    with open(SQL_FILE, "r", encoding="utf-8") as f:
        content = f.read().split('-- Seed default accounts')[0]
        matches = re.findall(r'\((\d+),\s*\'{"en": "[^"]+", "ru": "([^"]+)"}\'', content)
        for cat_id, ru_name in matches:
            categories[int(cat_id)] = ru_name
    return categories


def extract_unique_businesses():
    # Only target FibiSave files
    files = glob.glob(os.path.join(os.path.dirname(__file__), "..", "bank_statements", "Fibi*.xls*"))
    all_names = set()
    for file in files:
        try:
            df = pd.read_excel(file)
            col_name = None
            if 'Transaction' in df.columns:
                col_name = 'Transaction'
            else:
                # Sometimes the header is pushed down one row
                df2 = pd.read_excel(file, skiprows=1)
                if 'Transaction' in df2.columns:
                    df = df2
                    col_name = 'Transaction'
                    
            if col_name:
                for idx, row in df.iterrows():
                    val = row[col_name]
                    if pd.isna(val): continue
                    
                    if str(val).strip() == "CREDIT":
                        credit_amt = row.get('Credit', 0)
                        try:
                            amt = float(credit_amt)
                            if amt > 1000:
                                val = "CREDIT salary"
                            else:
                                val = "CREDIT allowances"
                        except (ValueError, TypeError):
                            pass
                            
                    if str(val).strip() == "TFR TO ANOTHER":
                        debit_amt = row.get('Debit', 0)
                        try:
                            amt = float(debit_amt)
                            if amt < 50:
                                val = "TFR TO ANOTHER kids"
                        except (ValueError, TypeError):
                            pass
                            
                    cleaned = clean_fibi_business_name(val)
                    if cleaned:
                        all_names.add(cleaned)
        except Exception as e:
            print(f"Skipping {os.path.basename(file)} or error: {e}")
            
    return list(all_names)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    existing_aliases = {}
    if os.path.exists(ALIASES_FILE):
        with open(ALIASES_FILE, "r", encoding="utf-8") as f:
            existing_aliases = yaml.safe_load(f) or {}

    print("Extracting business names from FIBI statements...")
    all_businesses = extract_unique_businesses()
    
    # Identify new ones and ignore credit card payments
    ignore_keywords = ["ISRACARD", "OPENING BALANCE"]
    new_businesses = []
    for b in all_businesses:
        if b in existing_aliases:
            continue
            
        should_ignore = False
        for kw in ignore_keywords:
            if kw.upper() in str(b).upper() or kw in str(b):
                should_ignore = True
                break
                
        if not should_ignore:
            new_businesses.append(b)
            
    print(f"{len(new_businesses)} are new and need categorization.")
    
    if not new_businesses:
        print("Nothing new to add.")
        return
        
    for name in sorted(new_businesses):
        existing_aliases[name] = None
                
    categories = get_categories_from_sql()
    comment = '# Categories Reference:\n'
    for cat_id, cat_name in sorted(categories.items()):
        comment += f'# {cat_id} = {cat_name}\n'
    comment += '#\n# Please replace null with the appropriate category ID for each business.\n\n'

    with open(ALIASES_FILE, "w", encoding="utf-8") as f:
        f.write(comment)
        yaml.dump(existing_aliases, f, allow_unicode=True, sort_keys=False)
        
    print(f"Done! Appended {len(new_businesses)} new aliases to data/aliases.yaml.")
    print("Please open data/aliases.yaml to assign categories.")

if __name__ == "__main__":
    main()
