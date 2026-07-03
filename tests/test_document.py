import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

try:
    from bot.handlers.document import document_handler, DEBOUNCE_JOBS
except ImportError:
    document_handler = None
    DEBOUNCE_JOBS = {}

@pytest.mark.asyncio
async def test_document_handler_success():
    """Test successful document upload and parsing via Telegram (debounced)."""
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
    status_msg = MagicMock()
    status_msg.edit_text = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=status_msg)
    
    # Context
    context = MagicMock()
    mock_file = AsyncMock()
    mock_file.download_to_drive = AsyncMock(return_value="temp_path.xlsx")
    context.bot.get_file = AsyncMock(return_value=mock_file)
    
    with patch("bot.handlers.document.import_excel_file") as mock_import, \
         patch("bot.handlers.document.save_transactions_bulk") as mock_save, \
         patch("bot.handlers.document.create_database_dump", new_callable=AsyncMock) as mock_backup, \
         patch("bot.handlers.document.check_access", return_value=True), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
         
        # Mock parsing returning 1 transaction
        mock_import.return_value = [{'date': '2026-05-06', 'amount': -10, 'description': 'Test', 'account_id': 2}]
        mock_save.return_value = 1 # 1 inserted row
        mock_backup.return_value = "/app/backups/db_backup_test.sql"
        
        await document_handler(update, context)
        
        # Await the debounce task to run the logic synchronously
        assert 123 in DEBOUNCE_JOBS
        task = DEBOUNCE_JOBS[123]['task']
        await task
        
        # Verify downloading
        context.bot.get_file.assert_called_once_with("file_123")
        
        # Verify backup was triggered
        mock_backup.assert_called_once()
        
        # Verify parsing was called with our hint from caption
        mock_import.assert_called_once_with("temp_imports/123_statement.xlsx", hint="isracard")
        
        # Verify save to db
        mock_save.assert_called_once()
        
        # Verify success message
        args, _ = status_msg.edit_text.call_args
        assert "✅" in args[0] or "успешно" in args[0].lower() or "завершен" in args[0].lower()


@pytest.mark.asyncio
async def test_document_handler_debounce_batch():
    """Test that sending multiple files in quick succession groups them."""
    if not document_handler:
        pytest.fail("document_handler not implemented yet")

    # Reset job tracking
    DEBOUNCE_JOBS.clear()

    # Mock context & file downloads
    context = MagicMock()
    mock_file = AsyncMock()
    context.bot.get_file = AsyncMock(return_value=mock_file)

    # Status message mock
    status_msg = MagicMock()
    status_msg.edit_text = AsyncMock()

    # First update
    update1 = MagicMock()
    update1.effective_user.id = 123
    update1.effective_user.language_code = "ru"
    # Need mock document structure
    doc1 = MagicMock()
    doc1.file_name = "statement1.xlsx"
    doc1.file_id = "file_1"
    update1.message.document = doc1
    update1.message.caption = None
    update1.message.reply_text = AsyncMock(return_value=status_msg)

    # Second update
    update2 = MagicMock()
    update2.effective_user.id = 123
    update2.effective_user.language_code = "ru"
    doc2 = MagicMock()
    doc2.file_name = "statement2.xlsx"
    doc2.file_id = "file_2"
    update2.message.document = doc2
    update2.message.caption = None
    update2.message.reply_text = AsyncMock(return_value=status_msg)

    original_sleep = asyncio.sleep
    with patch("bot.handlers.document.import_excel_file") as mock_import, \
         patch("bot.handlers.document.save_transactions_bulk") as mock_save, \
         patch("bot.handlers.document.create_database_dump", new_callable=AsyncMock) as mock_backup, \
         patch("bot.handlers.document.check_access", return_value=True), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        mock_import.side_effect = [
            [{'date': '2026-05-06', 'amount': -10, 'description': 'Tx1', 'account_id': 2}],
            [{'date': '2026-05-07', 'amount': -20, 'description': 'Tx2', 'account_id': 2}]
        ]
        mock_save.return_value = 2
        mock_backup.return_value = "/app/backups/db_backup_test.sql"

        # Trigger first document
        await document_handler(update1, context)
        task1 = DEBOUNCE_JOBS[123]['task']

        # Trigger second document immediately
        await document_handler(update2, context)
        task2 = DEBOUNCE_JOBS[123]['task']

        # Yield control to let the loop process the cancellation
        await original_sleep(0)
        assert task1.cancelled()

        # Await the second task to completion
        await task2

        # Verify bot.get_file was called for both
        assert context.bot.get_file.call_count == 2
        
        # Verify db backup was created EXACTLY once
        mock_backup.assert_called_once()
        
        # Verify saving was done in one batch
        mock_save.assert_called_once()
        saved_txs = mock_save.call_args[0][1]
        assert len(saved_txs) == 2

        # Verify status updates count
        status_msg.edit_text.assert_any_call(
            "⏳ Получено файлов: 2. Подготовка к обработке..."
        )
