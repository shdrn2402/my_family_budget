import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from telegram import InlineKeyboardMarkup
# We will create this handler next
# from bot.handlers.inline_menu import inline_menu_handler

@pytest.mark.asyncio
async def test_inline_menu_main_shows_transactions():
    """Test that clicking Edit Records shows buttons for each transaction."""
    from bot.handlers.inline_menu import inline_menu_handler
    
    update = MagicMock()
    update.callback_query = AsyncMock()
    update.callback_query.data = "edit_main:99,100"
    
    context = MagicMock()
    
    with patch("bot.handlers.inline_menu.get_db_connection") as mock_db:
        mock_conn = AsyncMock()
        mock_db.return_value.__aenter__.return_value = mock_conn
        mock_cur = AsyncMock()
        
        # Mock database returning 2 transactions
        mock_cur.fetchall.return_value = [
            {'id': 99, 'description': 'хлеб', 'amount': 50.0},
            {'id': 100, 'description': 'такси', 'amount': 300.0}
        ]
        
        mock_cursor_ctx = MagicMock()
        mock_cursor_ctx.__aenter__.return_value = mock_cur
        mock_conn.cursor = MagicMock(return_value=mock_cursor_ctx)
        
        # Call handler
        await inline_menu_handler(update, context)
        
        # Assert callback query was answered
        update.callback_query.answer.assert_called_once()
        
        # Assert reply markup was edited
        update.callback_query.edit_message_reply_markup.assert_called_once()
        
        kwargs = update.callback_query.edit_message_reply_markup.call_args[1]
        markup = kwargs['reply_markup']
        
        assert isinstance(markup, InlineKeyboardMarkup)
        keyboard = markup.inline_keyboard
        
        # Expecting a button for each transaction + Close button
        # [ [хлеб], [такси], [Закрыть] ] or [ [хлеб, такси], [Закрыть] ]
        # Let's assume one button per row for transactions
        assert len(keyboard) == 3
        assert "хлеб" in keyboard[0][0].text.lower()
        assert keyboard[0][0].callback_data == "edit_tx:99:99,100:"
        
        assert "такси" in keyboard[1][0].text.lower()
        assert keyboard[1][0].callback_data == "edit_tx:100:99,100:"
