import os
import re
import glob
import yaml
import pandas as pd
import sys

# Add the project root to sys.path so we can import from bot
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from bot.services.categorizer import clean_business_name
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
    files = glob.glob(os.path.join(os.path.dirname(__file__), "..", "bank_statements", "*.xlsx"))
    files += glob.glob(os.path.join(os.path.dirname(__file__), "..", "bank_statements", "*.xls"))
    
    all_names = set()
    for file in files:
        try:
            df = pd.read_excel(file)
            header_idx = None
            for idx, row in df.iterrows():
                row_str = " ".join(str(v) for v in row.values)
                if 'שם בית עסק' in row_str or 'תיאור' in row_str or 'Description' in row_str:
                    header_idx = idx
                    break
            
            if header_idx is not None:
                df = pd.read_excel(file, skiprows=header_idx + 1)
                col_name = None
                for col in df.columns:
                    col_s = str(col).strip()
                    if 'שם בית' in col_s or 'תיאור' in col_s or 'Description' in col_s:
                        col_name = col
                        break
                
                if col_name:
                    for val in df[col_name].dropna():
                        cleaned = clean_business_name(val)
                        if cleaned:
                            all_names.add(cleaned)
        except Exception as e:
            print(f"Skipping {os.path.basename(file)} or error: {e}")
            
    return list(all_names)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # To keep the YAML reading safe and clean
    existing_aliases = {}
    if os.path.exists(ALIASES_FILE):
        with open(ALIASES_FILE, "r", encoding="utf-8") as f:
            # We skip the comments when loading using safe_load
            existing_aliases = yaml.safe_load(f) or {}

    print("Extracting business names from statements...")
    all_businesses = extract_unique_businesses()
    print(f"Found {len(all_businesses)} unique clean business names.")
    
    # Identify new ones and filter out dynamic or technical names
    ignore_keywords = ["YELLOW", "פז", "דן דיל", 'סה"כ לחיוב', "שם בית עסק", "אלונית"]
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
        
    # Add new ones with null values
    for name in sorted(new_businesses):
        existing_aliases[name] = None
                
    # Update the file with the category reference comment at the top
    categories = get_categories_from_sql()
    comment = '# Categories Reference:\n'
    for cat_id, cat_name in sorted(categories.items()):
        comment += f'# {cat_id} = {cat_name}\n'
    comment += '#\n# Please replace null with the appropriate category ID for each business.\n\n'

    with open(ALIASES_FILE, "w", encoding="utf-8") as f:
        f.write(comment)
        yaml.dump(existing_aliases, f, allow_unicode=True, sort_keys=False)
        
    print(f"Done! Appended {len(new_businesses)} new aliases to data/aliases.yaml.")
    print("Please open data/aliases.yaml to assign categories to the new entries (marked as null).")

if __name__ == "__main__":
    main()
