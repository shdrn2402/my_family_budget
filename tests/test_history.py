import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.database import get_recent_transactions

@pytest.mark.asyncio
async def test_get_recent_transactions():
    """Test fetching recent transactions from DB."""
    mock_conn = MagicMock()
    mock_cur = AsyncMock()
    
    # Setup mock context manager for cursor
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
    
    # Mock database response
    mock_cur.fetchall.return_value = [
        {
            'id': 1,
            'description': 'кофе',
            'amount': 45.0,
            'date': '2026-05-03 10:00:00',
            'account_name': 'наличные'
        }
    ]
    
    result = await get_recent_transactions(12345, limit=10, conn=mock_conn)
    
    # Assert query was executed correctly
    mock_cur.execute.assert_called_once()
    assert "SELECT" in mock_cur.execute.call_args[0][0]
    
    # Assert result
    assert len(result) == 1
    assert result[0]['description'] == 'кофе'
    assert result[0]['amount'] == 45.0
@pytest.mark.asyncio
async def test_get_recent_transactions_pagination():
    """Test fetching transactions with offset."""
    mock_conn = MagicMock()
    mock_cur = AsyncMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
    
    await get_recent_transactions(12345, limit=5, offset=10, conn=mock_conn)
    
    # Check that LIMIT and OFFSET are in the query
    query = mock_cur.execute.call_args[0][0]
    params = mock_cur.execute.call_args[0][1]
    assert "LIMIT %s OFFSET %s" in query
    assert params == (12345, 5, 10)

@pytest.mark.asyncio
async def test_get_transactions_count():
    """Test counting transactions."""
    from bot.database import get_transactions_count
    mock_conn = MagicMock()
    mock_cur = AsyncMock()
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cur
    mock_cur.fetchone.return_value = {'count': 42}
    
    count = await get_transactions_count(12345, conn=mock_conn)
    
    assert count == 42
    mock_cur.execute.assert_called_once_with("SELECT COUNT(*) as count FROM transactions WHERE user_id = %s;", (12345,))
