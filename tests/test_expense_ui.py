# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.handlers.expense import expense_message_handler
# pyrefly: ignore [missing-import]
from telegram import InlineKeyboardMarkup

@pytest.mark.asyncio
async def test_expense_handler_sends_inline_keyboard():
    """Test that expense handler sends a combined message with an inline keyboard."""
    
    # Mock update and context
    update = MagicMock()
    update.message = AsyncMock()
    update.message.text = "хлеб нал 50, такси карта 300"
    update.effective_user.id = 123
    update.effective_user.language_code = "ru"
    
    context = MagicMock()
    
    # Mock check_access (allow access)
    with patch("bot.handlers.expense.check_access", new_callable=AsyncMock) as mock_check_access, \
         patch("bot.handlers.expense.get_db_connection") as mock_db, \
         patch("bot.database.get_user_info", new_callable=AsyncMock) as mock_user_info, \
         patch("bot.database.get_account_type", new_callable=AsyncMock) as mock_account_type, \
         patch("bot.handlers.expense.process_expense_text", new_callable=AsyncMock) as mock_process:
        
        mock_check_access.return_value = True
        mock_user_info.return_value = {'id': 123, 'name': 'Test User'}
        mock_account_type.return_value = 'cash'
        
        # Setup mock db context manager
        mock_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_conn
        mock_cur = AsyncMock()
        # Mock INSERT RETURNING id
        mock_cur.execute.return_value = None
        mock_cur.fetchone.return_value = {'id': 99}
        
        # cursor() is a sync method in psycopg that returns an async context manager
        mock_conn.cursor = MagicMock()
        mock_cursor_ctx = MagicMock()
        mock_cursor_ctx.__aenter__.return_value = mock_cur
        mock_conn.cursor.return_value = mock_cursor_ctx
        
        # Mock process_expense_text returning 2 valid items
        mock_process.return_value = [
            {
                'item_name': 'хлеб',
                'amount': 50.0,
                'account_id': 1,
                'account_alias': 'нал',
                'category_id': 2,
                'original': 'хлеб нал 50'
            },
            {
                'item_name': 'такси',
                'amount': 300.0,
                'account_id': 2,
                'account_alias': 'карта',
                'category_id': None,
                'original': 'такси карта 300'
            }
        ]
        
        # Call the handler
        await expense_message_handler(update, context)
        
        # Assert reply_text was called
        update.message.reply_text.assert_called_once()
        
        # Check arguments passed to reply_text
        call_args = update.message.reply_text.call_args
        text = call_args[0][0]
        kwargs = call_args[1]
        
        # 1. Check if the text contains total sum
        assert "350.00" in text, "Total sum should be in the message"
        
        # 2. Check if reply_markup was provided
        assert 'reply_markup' in kwargs, "Inline keyboard should be attached"
        markup = kwargs['reply_markup']
        assert isinstance(markup, InlineKeyboardMarkup), "Markup must be InlineKeyboardMarkup"
        
        # 3. Check if the button is the 'Edit Records' button
        keyboard = markup.inline_keyboard
        assert len(keyboard) > 0
        assert keyboard[0][0].text == "⚙️ Редактировать записи"
        assert keyboard[0][0].callback_data == "edit_main:99,99"
