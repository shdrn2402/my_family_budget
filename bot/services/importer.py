import pandas as pd
import os
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def parse_leumi(file_path):
    """
    Parses Bank Leumi .xls file.
    Format: Sheet 'Activities', Header starts at row 1.
    Columns: Balance, Value date, Credit, Debit, Transaction, Reference, Code, Date.
    """
    df = pd.read_excel(file_path, sheet_name='Activities', header=1, engine='xlrd')
    
    transactions = []
    for _, row in df.iterrows():
        # Skip empty rows or opening balance
        desc = str(row.get('Transaction', '')).strip()
        if not desc or 'OPENING BALANCE' in desc.upper():
            continue
            
        # Skip Isracard records to avoid duplicates
        if 'ISRACARD' in desc.upper():
            logger.info(f"Skipping Isracard record in Bank statement: {desc}")
            continue
            
        # Determine amount (Debit is negative, Credit is positive)
        debit = row.get('Debit')
        credit = row.get('Credit')
        
        amount = 0
        try:
            if pd.notnull(debit) and str(debit).strip() != '':
                amount = -abs(float(str(debit).replace(',', '')))
            elif pd.notnull(credit) and str(credit).strip() != '':
                amount = abs(float(str(credit).replace(',', '')))
        except ValueError:
            logger.warning(f"Could not parse amount from row: debit={debit}, credit={credit}")
            continue
            
        if amount == 0:
            continue
            
        # Parse date
        raw_date = row.get('Date')
        try:
            if isinstance(raw_date, datetime):
                date_obj = raw_date
            else:
                date_obj = datetime.strptime(str(raw_date), '%d/%m/%Y')
        except:
            logger.warning(f"Could not parse date: {raw_date}")
            continue

        transactions.append({
            'date': date_obj,
            'amount': amount,
            'description': desc,
            'external_id': f"leumi_{row.get('Reference', 'no_ref')}_{date_obj.strftime('%Y%m%d')}_{amount}",
            'account_id': 3, # Family Debit
            'source_type': 'import'
        })
        
    return transactions

def parse_isracard(file_path, account_id=2):
    """
    Parses Isracard .xlsx file.
    Contains multiple tables on one sheet.
    """
    # Read raw to find table boundaries
    raw_df = pd.read_excel(file_path, header=None, engine='openpyxl')
    
    transactions = []
    
    # Tables often start after these keywords
    # 1. 'עסקאות למועד חיוב' (Charges for payment date)
    # 2. 'עסקאות בחיוב מחוץ למועד' (Immediate charges/foreign)
    
    current_table_header_row = -1
    
    for i, row in raw_df.iterrows():
        row_list = [str(x) for x in row.tolist()]
        
        # Check if this is a header row
        if 'תאריך רכישה' in row_list and 'שם בית עסק' in row_list:
            # We found a table header!
            header_idx = row_list.index('תאריך רכישה')
            
            # Read from this point until the end of this table (usually indicated by total or empty row)
            # For simplicity, we just iterate rows from i+1 until we hit an empty row or a total
            for j in range(i + 1, len(raw_df)):
                sub_row = raw_df.iloc[j]
                
                # Stop if it looks like a total or end of table
                if pd.isnull(sub_row[header_idx]) or 'סה"כ' in str(sub_row.tolist()):
                    break
                
                # Extract data
                # Based on deep inspection:
                # 0: Date, 1: Description, 2: Amount, 3: Currency, 4: ChargeAmount, 5: ChargeCurrency, 6: Voucher (מס' שובר)
                try:
                    raw_date = str(sub_row[0])
                    # Format is DD.MM.YY
                    date_obj = datetime.strptime(raw_date, '%d.%m.%y')
                    
                    desc = str(sub_row[1])
                    try:
                        # Clean amount string from commas and spaces
                        clean_amount = str(sub_row[4]).replace(',', '').strip()
                        charge_amount = float(clean_amount)
                    except (ValueError, TypeError):
                        continue
                        
                    voucher = str(sub_row[6])
                    
                    transactions.append({
                        'date': date_obj,
                        'amount': -abs(charge_amount), # Always expense for cards in these tables
                        'description': desc,
                        'external_id': f"isracard_{voucher}",
                        'account_id': account_id,
                        'source_type': 'import'
                    })
                except Exception as e:
                    # logger.debug(f"Row {j} is not a valid transaction: {e}")
                    continue
                    
    return transactions

def import_excel_file(file_path, hint=None):
    """
    Detects file type based on hint (from Telegram caption) or filename patterns.
    - FibiSave -> Bank Leumi (Debit)
    - Starts with 4 digits -> Isracard (Credit)
    """
    filename = os.path.basename(file_path)
    search_text = (filename + (hint if hint else "")).lower()
    
    # Precise patterns
    if 'fibisave' in search_text or 'leumi' in search_text or 'benleumi' in search_text:
        return parse_leumi(file_path)
    
    # Isracard pattern: usually starts with 4 digits of the card
    # Check if filename starts with 4 digits (e.g. 4787...)
    match = re.match(r'^(\d{4})', filename)
    if match or 'isracard' in search_text:
        prefix = match.group(1) if match else ""
        
        # Mapping card suffixes to account IDs
        mapping = {
            '4787': 1, # Andrey Credit
            '6747': 2  # Katya Credit
        }
        
        target_account_id = mapping.get(prefix, 1) # Default to Andrey Credit if unknown
        return parse_isracard(file_path, account_id=target_account_id)
        
    logger.warning(f"Unknown file format: {filename} (hint: {hint})")
    return []
