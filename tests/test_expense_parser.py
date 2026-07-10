import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from bot.services.expense import parse_expense_message, resolve_amount_sign

def test_resolve_amount_sign():
    # 1. Income (parent_id=1) -> always positive
    assert resolve_amount_sign(-100, 1) == 100
    assert resolve_amount_sign(100, 1) == 100

    # 2. Transfers (parent_id=2) -> preserve sign
    assert resolve_amount_sign(100, 2) == 100
    assert resolve_amount_sign(-100, 2) == -100

    # 3. Expenses (any other parent_id) -> always negative
    assert resolve_amount_sign(100, 3) == -100
    assert resolve_amount_sign(-100, 3) == -100
    assert resolve_amount_sign(100, None) == -100

@pytest.mark.asyncio
async def test_parse_expense_dates():
    """Test that date keywords like yesterday and today are extracted properly."""
    mock_conn = MagicMock()
    
    # Mock DB functions to avoid database calls
    with patch('bot.services.expense.resolve_account', new_callable=AsyncMock) as mock_resolve_account:
        mock_resolve_account.return_value = 1
        with patch('bot.services.expense.resolve_category_from_alias', new_callable=AsyncMock) as mock_resolve_category:
            mock_resolve_category.return_value = 1
            with patch('bot.services.expense.get_local_date') as mock_get_local_date:
                mock_get_local_date.return_value = date(2026, 7, 8)
                
                # Test "вчера"
                results = await parse_expense_message("кофе вчера 15", 12345, mock_conn)
                assert len(results) == 1
                assert results[0]['item_name'] == "кофе"
                assert results[0]['amount'] == 15.0
                assert results[0].get('date') == "2026-07-07"
                
                # Test "today"
                results = await parse_expense_message("taxi today 50", 12345, mock_conn)
                assert len(results) == 1
                assert results[0]['item_name'] == "taxi"
                assert results[0]['amount'] == 50.0
                assert results[0].get('date') == "2026-07-08"


@pytest.mark.asyncio
async def test_parse_expense_currency_comment():
    """Test that currency names are ignored and not treated as comments."""
    mock_conn = MagicMock()
    
    with patch('bot.services.expense.resolve_account', new_callable=AsyncMock) as mock_resolve_account:
        mock_resolve_account.return_value = 1
        with patch('bot.services.expense.resolve_category_from_alias', new_callable=AsyncMock) as mock_resolve_category:
            mock_resolve_category.return_value = 1
            
            # Phrase with currency only -> comment should be None
            results = await parse_expense_message("ремонт в ванной бит 300 шекелей.", 12345, mock_conn)
            assert len(results) == 1
            assert 'error' not in results[0]
            assert results[0]['item_name'] == "ремонт в ванной"
            assert results[0]['amount'] == 300.0
            assert results[0].get('comment') is None
            
            # Phrase with currency and actual comment -> currency stripped, comment kept
            results = await parse_expense_message("подарок 300 шекелей на день рождения", 12345, mock_conn)
            assert len(results) == 1
            assert 'error' not in results[0]
            assert results[0]['item_name'] == "подарок"
            assert results[0]['amount'] == 300.0
            assert results[0].get('comment') == "на день рождения"
            
            # Different currency symbol
            results = await parse_expense_message("обед 50 usd", 12345, mock_conn)
            assert len(results) == 1
            assert results[0].get('comment') is None
