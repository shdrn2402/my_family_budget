import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bot.services.voice import transcribe_voice

@pytest.mark.asyncio
async def test_transcribe_voice():
    """Test voice transcription using mocked API."""
    # Fake audio bytes
    fake_audio = b"fake_ogg_data"
    
    # We will mock the httpx.AsyncClient.post method
    with patch("bot.services.voice.httpx.AsyncClient.post") as mock_post:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Gemini API response format
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "купил кофе за 500 рублей наличными"}
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Call the function
        result = await transcribe_voice(fake_audio)
        
        # Assert the API was called
        mock_post.assert_called_once()
        
        # Assert the result is correct
        assert result == "купил кофе за 500 рублей наличными"

@pytest.mark.asyncio
async def test_voice_handler_uses_manual_voice_source_type():
    """Test that voice handler passes 'manual_voice' to save_expense_item."""
    from bot.handlers.voice import voice_message_handler
    
    update = MagicMock()
    update.message.voice.file_id = "test_file_id"
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 123
    update.effective_user.language_code = "en"
    
    context = MagicMock()
    mock_file = AsyncMock()
    mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"test"))
    context.bot.get_file = AsyncMock(return_value=mock_file)
    
    with patch("bot.handlers.voice.check_access", return_value=True), \
         patch("bot.handlers.voice.transcribe_voice", return_value="coffee cash 15"), \
         patch("bot.handlers.voice.get_db_connection") as mock_db, \
         patch("bot.handlers.voice.process_expense_text") as mock_process, \
         patch("bot.database.get_user_info", new_callable=AsyncMock) as mock_user_info, \
         patch("bot.services.expense.save_expense_item", new_callable=AsyncMock) as mock_save:
         
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock()
        mock_conn.commit = AsyncMock()
        mock_db.return_value = mock_conn
        
        mock_process.return_value = [{
            'item_name': 'coffee',
            'amount': 15.0,
            'account_id': 4,
            'account_alias': 'cash',
            'category_id': 1
        }]
        
        mock_save.return_value = {"id": 1, "db_amount": -15.0, "status": "confirmed"}
        
        await voice_message_handler(update, context)
        
        # Verify save_expense_item was called
        mock_save.assert_called_once()
        args, _ = mock_save.call_args
        
        # The 5th argument should be 'manual_voice'
        assert args[4] == 'manual_voice'
