import re
import pandas as pd
from typing import Optional

def clean_business_name(name: str) -> str:
    """
    Cleans a raw business name from bank statements by removing numbers, 
    legal suffixes, and standardizing big brand names.
    """
    if pd.isna(name) or not name:
        return ""
        
    fibi_clean = clean_fibi_business_name(name)
    if fibi_clean and fibi_clean != str(name).strip():
        return fibi_clean
        
    # Remove digits, periods, dashes, asterisks
    clean = re.sub(r'[\d\.\-\*]+', ' ', str(name).upper())
    # Remove specific unneeded terms
    clean = clean.replace('עסקה באילת', '').replace('תשלום', '')
    # Collapse multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    if not clean:
        return ""
        
    # 1. Pango
    if "פנגו מוביט" in clean or "תחבורה" in clean:
        if "פנגו" in clean or "מוביט" in clean:
            return "פנגו תחבורה ציבורית"
    if clean.startswith("פנגו"):
        return "פנגו חניה וכבישים"
        
    # 2. Global Services
    for svc in ["GOOGLE", "PAYPAL", "APPLE"]:
        if clean.startswith(svc):
            return svc
            
    # 3. Big Brands
    brands = [
        "סופר פארם", "טיב טעם", "יוחננוף", "מקדונלד'ס", "מקדולנדס",
        "גולדה", "ארומה", "KSP", "קיי אס פי", "איקאה", "IKEA", 
        "יאשקה", "קרלו", "סיטי מרקט", "CARREFOUR", "carrefour",
        "KFC", "אחוזת החוף", "אחוזות החוף", "הום סנטר", "נוי השדה",
        "עולם הממתקים", "פאפא ג'ונס", "בלו בדרך שלך",
        "סוויט טיים", "גוד פארם", "רולדין", "אי אם פי אם", "צ'וקה",
        "זארה", "ללין", "פליינג טייגר"
    ]
    
    for brand in brands:
        if clean.startswith(brand) or brand in clean:
            if brand in ["מקדולנדס", "מקדונלד'ס"]:
                return "מקדונלד'ס"
            if brand in ["KSP", "קיי אס פי"]:
                return "KSP"
            if brand in ["איקאה", "IKEA"]:
                return "IKEA"
            if brand in ["CARREFOUR", "carrefour"]:
                return "CARREFOUR"
            if brand in ["אחוזת החוף", "אחוזות החוף"]:
                return "אחוזת החוף"
            if brand == "פאפא ג'ונס":
                return "פאפא גונס"
            return brand
            
    # 3.5 Dynamic rules
    if clean.startswith("חניון "):
        return "חניון"

    # 4. Legal suffixes
    for suffix in ['בע"מ', 'בעמ', 'בע?מ', 'בע']:
        if clean.endswith(" " + suffix):
            clean = clean[:-len(suffix)-1].strip()
            
    return clean if len(clean) > 1 else ""

def clean_fibi_business_name(name: str) -> str:
    """
    Cleans Bank Leumi (FibiSave) specific business names,
    stripping numbers from known ATM, check, and transfer prefixes.
    """
    if pd.isna(name): return ""
    clean = str(name).strip()
    
    # Strip numbers from known ATM, check, and transfer prefixes
    prefixes = [
        "CHQ.WITHD", "BANKAT", "DISC CASPO", "LEUM CASPO", 
        "MATRIX ATM'S", "SHIUN", "SNIFOMAT", "ATM CASH DEPOSIT", 
        "IMMEDIATE TRANSFER", "ARREAR", "INTEREST ", "INT.M ",
        "CREDIT PLUS ", "LOAN PYMT "
    ]
    for p in prefixes:
        if clean.startswith(p):
            return p.strip()
            
    return clean if len(clean) > 1 else ""

def auto_categorize(raw_name: str, amount: float, db_aliases: dict[str, int]) -> Optional[int]:
    """
    Categorizes a transaction based on its raw name and amount.
    First cleans the name, then applies dynamic threshold rules, 
    and falls back to dictionary lookup.
    """
    clean_name = clean_business_name(raw_name)
    if not clean_name:
        return None
        
    abs_amount = abs(amount)
    
    # Dynamic Rules for YELLOW / אלונית / פז
    if any(keyword in clean_name for keyword in ["YELLOW", "אלונית", "פז"]):
        if abs_amount > 100.0:
            return 26  # Топливо / Fuel
        else:
            return 17  # Снеки / Snacks
            
    # Dynamic Rules for Dan Deal
    if "דן דיל" in clean_name:
        if abs_amount > 50.0:
            return 24  # Хозтовары / Household
        else:
            return 17  # Сладости / Snacks

    # Fallback to standard dictionary lookup
    
    # 1. Look for exact match with cleaned name
    if clean_name in db_aliases:
        return db_aliases[clean_name]
        
    # 2. Look for exact match with raw name (some DB aliases were saved with punctuation)
    raw_upper = str(raw_name).strip().upper()
    # Create a dict with uppercase keys for case-insensitive exact matching
    db_aliases_upper = {k.upper(): v for k, v in db_aliases.items()}
    if raw_upper in db_aliases_upper:
        return db_aliases_upper[raw_upper]
        
    # 3. Look for partial match
    for alias_name, category_id in db_aliases.items():
        alias_upper = alias_name.upper()
        if alias_upper in clean_name or clean_name in alias_upper or alias_upper in raw_upper or raw_upper in alias_upper:
            return category_id
            
    return None
