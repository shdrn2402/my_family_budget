import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.handlers.expense import expense_message_handler

@pytest.mark.asyncio
async def test_expense_handler_allows_cash_entry():
    """Test that manual entry is allowed for cash accounts."""
    update = MagicMock()
    update.message.text = "coffee cash 10"
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 123
    update.effective_user.language_code = "en"
    context = MagicMock()
    
    # Mock dependencies
    with patch("bot.handlers.expense.get_db_connection") as mock_db, \
         patch("bot.handlers.expense.process_expense_text") as mock_process, \
         patch("bot.database.get_user_info", new_callable=AsyncMock) as mock_user_info, \
         patch("bot.database.get_account_type", new_callable=AsyncMock) as mock_get_type, \
         patch("bot.handlers.expense.check_access", return_value=True):
         
        mock_user_info.return_value = {'id': 123, 'name': 'Test'}
         
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_conn.commit = AsyncMock()
        mock_db.return_value = mock_conn
        
        mock_cur = MagicMock()
        mock_cur.__aenter__ = AsyncMock(return_value=mock_cur)
        mock_cur.__aexit__ = AsyncMock()
        mock_cur.execute = AsyncMock()
        mock_cur.fetchone = AsyncMock(return_value={'id': 999})
        mock_conn.cursor.return_value = mock_cur
        
        # Mock parsed item
        mock_process.return_value = [{
            'item_name': 'coffee',
            'amount': 10.0,
            'account_id': 3,
            'account_alias': 'cash',
            'category_id': 1
        }]
        
        # Mock account type as 'cash'
        mock_get_type.return_value = 'cash'
        
        await expense_message_handler(update, context)
        
        # Verify it tried to insert into DB
        update.message.reply_text.assert_called_once()
        args, _ = update.message.reply_text.call_args
        assert "✅" in args[0]
        assert "coffee" in args[0]

@pytest.mark.asyncio
async def test_expense_handler_blocks_card_entry():
    """Test that manual entry is blocked for card accounts."""
    update = MagicMock()
    update.message.text = "coffee card 10"
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 123
    update.effective_user.language_code = "en"
    context = MagicMock()
    
    # Mock dependencies
    with patch("bot.handlers.expense.get_db_connection") as mock_db, \
         patch("bot.handlers.expense.process_expense_text") as mock_process, \
         patch("bot.database.get_account_type", new_callable=AsyncMock) as mock_get_type, \
         patch("bot.handlers.expense.check_access", return_value=True):
         
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_db.return_value = mock_conn
        
        mock_cur = MagicMock()
        mock_cur.__aenter__ = AsyncMock(return_value=mock_cur)
        mock_cur.__aexit__ = AsyncMock()
        mock_cur.execute = AsyncMock()
        mock_conn.cursor.return_value = mock_cur
        
        # Mock parsed item
        mock_process.return_value = [{
            'item_name': 'coffee',
            'amount': 10.0,
            'account_id': 1,
            'account_alias': 'card',
            'category_id': 1
        }]
        
        # Mock account type as 'card'
        mock_get_type.return_value = 'card'
        
        await expense_message_handler(update, context)
        
        # Verify the reply contains the "denied" message
        update.message.reply_text.assert_called_once()
        args, _ = update.message.reply_text.call_args
        assert "⚠️" in args[0]
        assert "bank statements only" in args[0]
        
        # Verify NO insertion attempt
        for call in mock_cur.execute.call_args_list:
            assert "INSERT INTO transactions" not in call[0][0]
