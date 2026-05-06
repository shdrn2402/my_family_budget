import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from telegram import InlineKeyboardMarkup
from bot.handlers.history import history_handler, build_history_page

@pytest.mark.asyncio
async def test_history_handler_sends_message():
    """Test that /history command sends a paginated message."""
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.language_code = "ru"
    update.message = AsyncMock()
    context = MagicMock()
    
    with patch("bot.handlers.history.build_history_page") as mock_build:
        mock_build.return_value = ("some text", InlineKeyboardMarkup([]))
        await history_handler(update, context)
        
        update.message.reply_text.assert_called_once()
        args, kwargs = update.message.reply_text.call_args
        assert args[0] == "some text"
        assert kwargs['reply_markup'] is not None

@pytest.mark.asyncio
async def test_build_history_page_first_page_of_many():
    """Test pagination buttons on the first page when there are more pages."""
    user_id = 123
    lang = "ru"
    
    with patch("bot.handlers.history.get_recent_transactions") as mock_get_tx, \
         patch("bot.handlers.history.get_transactions_count") as mock_count:
         
        mock_get_tx.return_value = [
            {'id': i, 'description': f'item {i}', 'amount': 100, 'date': MagicMock(), 'account_name': 'acc'}
            for i in range(1, 6)
        ]
        mock_count.return_value = 12 # 3 pages (5, 5, 2)
        
        text, markup = await build_history_page(user_id, lang, page=0)
        
        assert "item 1" in text
        assert "item 5" in text
        
        keyboard = markup.inline_keyboard
        nav_row = keyboard[0]
        
        # [ "1/3", "➡️" ] - since page 0, no Back button
        assert len(nav_row) == 2
        assert "1/3" in nav_row[0].text
        assert nav_row[1].callback_data == "hist_page:1"
        
        # Check edit button IDs (with page suffix)
        edit_button = keyboard[1][0]
        assert "edit_main:1,2,3,4,5:0" in edit_button.callback_data

@pytest.mark.asyncio
async def test_build_history_page_middle_page():
    """Test pagination buttons on a middle page."""
    user_id = 123
    lang = "ru"
    
    with patch("bot.handlers.history.get_recent_transactions") as mock_get_tx, \
         patch("bot.handlers.history.get_transactions_count") as mock_count:
         
        mock_get_tx.return_value = [
            {'id': i, 'description': f'item {i}', 'amount': 100, 'date': MagicMock(), 'account_name': 'acc'}
            for i in range(6, 11)
        ]
        mock_count.return_value = 12
        
        text, markup = await build_history_page(user_id, lang, page=1)
        
        keyboard = markup.inline_keyboard
        nav_row = keyboard[0]
        
        # [ "⬅️", "2/3", "➡️" ]
        assert len(nav_row) == 3
        assert nav_row[0].callback_data == "hist_page:0"
        assert "2/3" in nav_row[1].text
        assert nav_row[2].callback_data == "hist_page:2"

@pytest.mark.asyncio
async def test_build_history_page_last_page():
    """Test pagination buttons on the last page."""
    user_id = 123
    lang = "ru"
    
    with patch("bot.handlers.history.get_recent_transactions") as mock_get_tx, \
         patch("bot.handlers.history.get_transactions_count") as mock_count:
         
        mock_get_tx.return_value = [
            {'id': 11, 'description': 'item 11', 'amount': 100, 'date': MagicMock(), 'account_name': 'acc'}
        ]
        mock_count.return_value = 11 # 3 pages (5, 5, 1)
        
        text, markup = await build_history_page(user_id, lang, page=2)
        
        keyboard = markup.inline_keyboard
        nav_row = keyboard[0]
        
        # [ "⬅️", "3/3" ] - no Next button
        assert len(nav_row) == 2
        assert nav_row[0].callback_data == "hist_page:1"
        assert "3/3" in nav_row[1].text

@pytest.mark.asyncio
async def test_inline_menu_handles_hist_page():
    """Test that clicking a pagination button updates the history message."""
    from bot.handlers.inline_menu import inline_menu_handler
    
    update = MagicMock()
    update.callback_query = AsyncMock()
    update.callback_query.data = "hist_page:1"
    update.effective_user.id = 123
    update.effective_user.language_code = "ru"
    
    context = MagicMock()
    
    with patch("bot.handlers.history.build_history_page") as mock_build:
        mock_build.return_value = ("new text", InlineKeyboardMarkup([]))
        
        await inline_menu_handler(update, context)
        
        update.callback_query.edit_message_text.assert_called_once()
        args, kwargs = update.callback_query.edit_message_text.call_args
        assert args[0] == "new text"
