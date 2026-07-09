import sys
import os
import csv
import glob

# Add the project root to sys.path so we can import from bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.services.importer import parse_bit_csv

def generate_csv():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern = os.path.join(base_dir, 'bank_statements', 'bit_transactions_*.csv')
    files = glob.glob(pattern)
    
    if not files:
        print("No bit_transactions_*.csv files found in bank_statements/")
        return

    all_transactions = []
    
    for file_path in files:
        print(f"Parsing {os.path.basename(file_path)}...")
        # account_id doesn't strictly matter for historical load if it's from Transit, 
        # but 1 (Andrey Credit) is a safe default for 'כרטיס אשראי'
        txs = parse_bit_csv(file_path, account_id=1)
        all_transactions.extend(txs)
        
    if not all_transactions:
        print("No valid transactions found.")
        return

    # Sort by date
    all_transactions.sort(key=lambda x: x['date'])
    
    output_path = os.path.join(base_dir, 'bank_statements', 'legacy_bit_transactions_2024_2026.csv')
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['date', 'amount', 'description', 'comment', 'account_id', 'category_id'])
        
        for tx in all_transactions:
            writer.writerow([
                tx['date'].strftime('%Y-%m-%d'),
                tx['amount'],
                tx['description'],
                tx['comment'],
                tx['account_id'],
                ''  # Empty category_id for manual filling
            ])
            
    print(f"\nGenerated {output_path} with {len(all_transactions)} transactions.")
    print("Please open this file in Excel, fill in the 'category_id' column, and then we will load it into the DB.")

if __name__ == '__main__':
    generate_csv()
