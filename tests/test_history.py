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
    
    result = await get_recent_transactions(12345, 10, mock_conn)
    
    # Assert query was executed correctly
    mock_cur.execute.assert_called_once()
    assert "SELECT" in mock_cur.execute.call_args[0][0]
    
    # Assert result
    assert len(result) == 1
    assert result[0]['description'] == 'кофе'
    assert result[0]['amount'] == 45.0
