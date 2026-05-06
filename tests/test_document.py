import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# We will implement this handler in bot/handlers/document.py
try:
    from bot.handlers.document import document_handler
except ImportError:
    document_handler = None

@pytest.mark.asyncio
async def test_document_handler_success():
    """Test successful document upload and parsing via Telegram."""
    if not document_handler:
        pytest.fail("document_handler not implemented yet")
        
    update = MagicMock()
    # Mock document
    doc = MagicMock()
    doc.file_name = "statement.xlsx"
    doc.file_id = "file_123"
    update.message.document = doc
    
    # Mock caption (user hint)
    update.message.caption = "isracard"
    
    # Mock user
    update.effective_user.id = 123
    update.effective_user.language_code = "ru"
    
    # Mock message replies
    update.message.reply_text = AsyncMock()
    
    # Context
    context = MagicMock()
    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock(return_value="temp_path.xlsx")
    context.bot.get_file = AsyncMock(return_value=mock_file)
    
    with patch("bot.handlers.document.import_excel_file") as mock_import, \
         patch("bot.handlers.document.save_transactions_bulk") as mock_save, \
         patch("bot.handlers.document.check_access", return_value=True):
         
        # Mock parsing returning 1 transaction
        mock_import.return_value = [{'date': '2026-05-06', 'amount': -10, 'description': 'Test', 'account_id': 2}]
        mock_save.return_value = 1 # 1 inserted row
        
        await document_handler(update, context)
        
        # Verify downloading
        context.bot.get_file.assert_called_once_with("file_123")
        mock_file.download_to_drive.assert_called_once()
        
        # Verify parsing was called with our hint from caption
        mock_import.assert_called_once_with("temp_path.xlsx", hint="isracard")
        
        # Verify save to db
        mock_save.assert_called_once()
        
        # Verify success message
        args, _ = update.message.reply_text.call_args
        assert "Успешно" in args[0] or "успешно" in args[0]
