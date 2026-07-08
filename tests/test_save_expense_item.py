import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from bot.services.expense import save_expense_item


@pytest.mark.asyncio
async def test_save_expense_cash_expense():
    """Test saving a standard cash expense."""
    item = {
        'item_name': 'coffee',
        'amount': 15.0,
        'account_id': 4,
        'account_alias': 'cash',
        'category_id': 1,
        'comment': None,
        'original': 'coffee 15 cash'
    }
    
    mock_conn = MagicMock()
    mock_cursor = AsyncMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    
    # Mock get_account_type to return 'cash'
    with patch('bot.services.expense.get_account_type', new_callable=AsyncMock) as mock_get_type:
        mock_get_type.return_value = 'cash'
        
        # Mock get_text to just return the key for simplicity in assertions
        with patch('bot.services.expense.get_text', side_effect=lambda key, lang, **kwargs: key):
            # Mock get_local_date to return a fixed date
            with patch('bot.services.expense.get_local_date') as mock_get_local_date:
                mock_get_local_date.return_value = date(2026, 7, 8)
                # Mock the fetchone to return a dummy ID
                mock_cursor.fetchone.return_value = {'id': 100}
                
                result = await save_expense_item(item, 12345, 'en', mock_conn, 'manual_text')
                
                assert 'error' not in result
                assert result['id'] == 100
                assert result['db_amount'] == -15.0  # Should be negative
                assert result['status'] == 'confirmed'
                
                # Verify that execute was called with correct db_amount and date
                args, kwargs = mock_cursor.execute.call_args
                assert args[1][3] == -15.0
                assert args[1][6] == "2026-07-08"  # Should use get_local_date


@pytest.mark.asyncio
async def test_save_expense_income():
    """Test saving an income transaction."""
    item = {
        'item_name': 'salary',
        'amount': 100.0,
        'account_id': 1,
        'account_alias': 'bank',
        'category_id': 11,  # Income category
        'comment': None,
        'original': 'salary 5000 bank'
    }
    
    mock_conn = MagicMock()
    mock_cursor = AsyncMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    
    with patch('bot.services.expense.get_account_type', new_callable=AsyncMock) as mock_get_type:
        mock_get_type.return_value = 'card'
        
        with patch('bot.services.expense.get_text', side_effect=lambda key, lang, **kwargs: key):
            mock_cursor.fetchone.return_value = {'id': 101}
            
            result = await save_expense_item(item, 12345, 'en', mock_conn, 'manual_text')
            
            assert 'error' not in result
            assert result['db_amount'] == 100.0  # Should be positive
            
            # Since it's a card and > 150, but it is income, we might just let it be pending or confirmed based on logic.
            # Assuming income is also limited or not limited, let's just check the amount sign here.

@pytest.mark.asyncio
async def test_save_expense_card_over_limit():
    """Test saving a card expense over the 150 limit."""
    item = {
        'item_name': 'groceries',
        'amount': 200.0,
        'account_id': 2,
        'account_alias': 'card',
        'category_id': 2,
        'comment': None,
        'original': 'groceries 200 card'
    }
    
    mock_conn = MagicMock()
    
    with patch('bot.services.expense.get_account_type', new_callable=AsyncMock) as mock_get_type:
        mock_get_type.return_value = 'card'
        
        with patch('bot.services.expense.get_text', side_effect=lambda key, lang, **kwargs: key):
            result = await save_expense_item(item, 12345, 'en', mock_conn, 'manual_text')
            
            assert 'error' in result
            assert result['error'] == 'card_limit_exceeded'

@pytest.mark.asyncio
async def test_save_expense_missing_account():
    """Test saving an expense without an account."""
    item = {
        'item_name': 'coffee',
        'amount': 15.0,
        'account_id': None,
        'account_alias': 'unknown',
        'category_id': 1,
        'comment': None,
        'original': 'coffee 15 unknown'
    }
    
    mock_conn = MagicMock()
    
    with patch('bot.services.expense.get_text', side_effect=lambda key, lang, **kwargs: key):
        result = await save_expense_item(item, 12345, 'en', mock_conn, 'manual_text')
        
        assert 'error' in result
        assert result['error'] == 'account_not_found'
