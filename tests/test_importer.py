import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch
from bot.services.importer import parse_leumi, parse_isracard, import_excel_file, parse_bit_csv

def test_parse_leumi_success():
    """Test standard Bank Leumi statement parsing, checking that Isracard entries are ignored."""
    # Mock data mimicking the Leumi Excel structure
    # Columns: Balance, Value date, Credit, Debit, Transaction, Reference, Code, Date
    data = {
        'Balance': [1000, 900, 800, 850],
        'Value date': ['10/03/2026', '11/03/2026', '12/03/2026', '13/03/2026'],
        'Credit': [None, None, None, 50],
        'Debit': [None, 100, 50, None],
        'Transaction': ['OPENING BALANCE', 'SUPERMARKET', 'ISRACARD - 5883', 'REFUND'],
        'Reference': ['123', '456', '789', '012'],
        'Code': [1, 2, 3, 4],
        'Date': ['10/03/2026', '11/03/2026', '12/03/2026', '13/03/2026']
    }
    mock_df = pd.DataFrame(data)

    with patch('pandas.read_excel', return_value=mock_df):
        transactions = parse_leumi("dummy_benleumi.xls")
        
        # We expect: 
        # 1. OPENING BALANCE to be ignored
        # 2. ISRACARD to be ignored
        # 3. SUPERMARKET to be parsed as an expense (-100)
        # 4. REFUND to be parsed as income (50)
        assert len(transactions) == 2
        
        # Verify SUPERMARKET
        assert transactions[0]['description'] == 'SUPERMARKET'
        assert transactions[0]['amount'] == -100.0
        assert transactions[0]['account_id'] == 3 # Debit
        assert transactions[0]['source_type'] == 'import_xls'
        
        # Verify REFUND
        assert transactions[1]['description'] == 'REFUND'
        assert transactions[1]['amount'] == 50.0

def test_parse_isracard_success():
    """Test Isracard statement parsing with multiple internal tables."""
    # Mock data mimicking the raw read of an Isracard Excel
    # In raw read, header is None, so we simulate rows as lists
    data = [
        ['פירוט עסקאות', None, 'אפריל 2026', None, None, None, None, None],
        ['עסקאות למועד חיוב', None, None, None, None, None, None, None],
        ['תאריך רכישה', 'שם בית עסק', 'סכום עסקה', 'מטבע עסקה', 'סכום חיוב', 'מטבע חיוב', "מס' שובר", 'פירוט נוסף'],
        ['10.04.26', 'Coffee Shop', 15.0, '₪', 15.0, '₪', '123456', None],
        ['11.04.26', 'Supermarket', 100.0, '₪', 100.0, '₪', '789012', None],
        [None, 'סה"כ לחיוב החודש בכרטיס בש"ח', None, None, 115.0, '₪', None, None],
        ['עסקאות בחיוב מחוץ למועד', None, None, None, None, None, None, None],
        ['תאריך רכישה', 'שם בית עסק', 'סכום עסקה', 'מטבע עסקה', 'סכום חיוב', 'מטבע חיוב', "מס' שובר", 'פירוט נוסף', 'חיוב בחשבון הבנק'],
        ['12.04.26', 'Netflix', 10.0, '$', 38.0, '₪', '999999', None, '12.04.26']
    ]
    mock_df = pd.DataFrame(data)
    
    with patch('pandas.read_excel', return_value=mock_df):
        transactions = parse_isracard("dummy_isracard.xlsx")
        
        # We expect 3 valid transactions
        assert len(transactions) == 3
        
        # Verify first transaction
        assert transactions[0]['description'] == 'Coffee Shop'
        assert transactions[0]['amount'] == -15.0
        assert transactions[0]['account_id'] == 2 # Credit
        assert transactions[0]['external_id'] == 'isracard_123456'
        
        # Verify the foreign transaction from the second table
        assert transactions[2]['description'] == 'Netflix'
        assert transactions[2]['amount'] == -38.0 # Should use 'סכום חיוב' (charge amount in local currency)

def test_parse_bit_csv_success():
    """Test parsing of Bit CSV format."""
    # Columns: Status, Description, Fee Amount, Amount, Payment Method, Credit/Debit, From/To, Date
    data = {
        'Status': ['Done', 'Done', 'Done', 'Expired', 'Done', 'Done'],
        'Description': ['Withdrawal to bank account', 'העברת כספים bit', 'העברת כספים bit', 'העברת כספים bit', 'העברת כספים bit', 'עזרה'],
        'Fee Amount': [0, 0, 0, 0, 0, 0],
        'Amount': [300, 50, 540, 9, 200, 500],
        'Payment Method': ['חשבון בנק', 'יתרה', 'כרטיס אשראי', 'יתרה', 'יתרה', 'חשבון בנק'],
        'Credit/Debit': ['Credit', 'Credit', 'Debit', 'Debit', 'Debit', 'Credit'],
        'From/To': ['אנדריי שדרין', 'אלבינה קושניר', 'אלה בילמוס', 'לב פיין', 'someone', 'אלכסנדר מורוז'],
        'Date': ['30.01.26', '26.05.26', '16.04.26', '01.06.26', '12.06.26', '11.07.24']
    }
    mock_df = pd.DataFrame(data)
    
    with patch('pandas.read_csv', return_value=mock_df):
        transactions = parse_bit_csv("bit_transactions_2026.csv", account_id=1) # Account id for credit card fallback
        
        # 5 valid input rows, but 'Withdrawal' creates 2 lines, so 6 output rows expected
        assert len(transactions) == 6
        
        # 1. Withdrawal to bank account (Row 1 -> Creates 2 lines)
        # Line 1: Expense from Transit
        assert transactions[0]['description'] == 'Withdrawal to bank account'
        assert transactions[0]['amount'] == -300.0
        assert transactions[0]['account_id'] == 5 # Transit
        
        # Line 2: Income to Bank
        assert transactions[1]['description'] == 'Withdrawal to bank account'
        assert transactions[1]['amount'] == 300.0
        assert transactions[1]['account_id'] == 3 # Family Debit
        
        # 2. Receipt to balance (יתרה, Credit)
        assert transactions[2]['amount'] == 50.0
        assert transactions[2]['account_id'] == 5 # Transit
        
        # 3. Expense from Credit Card
        assert transactions[3]['amount'] == -540.0
        assert transactions[3]['account_id'] == 1 # Passed as argument
        
        # 4. Expense from Balance (יתרה, Debit)
        assert transactions[4]['amount'] == -200.0
        assert transactions[4]['account_id'] == 5 # Transit
        
        # 5. Direct Income (חשבון בנק, Credit) -> 'עזרה'
        assert transactions[5]['amount'] == 500.0
        assert transactions[5]['account_id'] == 3 # Family Debit

def test_import_excel_file_routing():
    """Test that the main router correctly identifies file types based on new patterns."""
    with patch('bot.services.importer.parse_leumi') as mock_leumi, \
         patch('bot.services.importer.parse_isracard') as mock_isra:
         
        # Test Bank Leumi (FibiSave)
        import_excel_file("FibiSave_Activities.xls")
        mock_leumi.assert_called_once()
        mock_isra.assert_not_called()
        
        mock_leumi.reset_mock()
        
        # Test Isracard (starts with 4787)
        import_excel_file("4787_isracard_report.xlsx")
        mock_isra.assert_called_with("4787_isracard_report.xlsx", account_id=1)
        
        mock_isra.reset_mock()

        # Test Isracard (starts with 6747 - Wife)
        import_excel_file("6747_wife_report.xlsx")
        mock_isra.assert_called_with("6747_wife_report.xlsx", account_id=2)

    with patch('bot.services.importer.parse_bit_csv') as mock_bit:
        import_excel_file("bit_transactions_2026.csv")
        mock_bit.assert_called_with("bit_transactions_2026.csv", account_id=1)
