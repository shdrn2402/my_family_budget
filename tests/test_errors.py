import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers.errors import error_handler

@pytest.mark.asyncio
async def test_error_handler_notifies_user_ru():
    """Test that the global error handler notifies the user in Russian."""
    
    # Mock Update
    update = MagicMock()
    update.effective_user.language_code = "ru"
    update.effective_message = AsyncMock()
    
    # Mock Context with an error
    context = MagicMock()
    context.error = ValueError("Test explosion")
    
    # Call handler
    await error_handler(update, context)
    
    # Assert reply was sent
    update.effective_message.reply_text.assert_called_once()
    args = update.effective_message.reply_text.call_args[0]
    assert "Произошла ошибка" in args[0]

@pytest.mark.asyncio
async def test_error_handler_notifies_user_en():
    """Test that the global error handler notifies the user in English."""
    
    # Mock Update
    update = MagicMock()
    update.effective_user.language_code = "en"
    update.effective_message = AsyncMock()
    
    # Mock Context with an error
    context = MagicMock()
    context.error = Exception("Unexpected")
    
    # Call handler
    await error_handler(update, context)
    
    # Assert reply was sent
    update.effective_message.reply_text.assert_called_once()
    args = update.effective_message.reply_text.call_args[0]
    assert "An error occurred" in args[0]

@pytest.mark.asyncio
async def test_error_handler_no_message_silent_fail():
    """Test that error handler doesn't crash if message cannot be sent."""
    update = MagicMock()
    update.effective_user.language_code = "ru"
    update.effective_message = AsyncMock()
    update.effective_message.reply_text.side_effect = Exception("Telegram Blocked")
    
    context = MagicMock()
    context.error = ValueError("Boom")
    
    # Should not raise exception
    await error_handler(update, context)
    
    update.effective_message.reply_text.assert_called_once()
