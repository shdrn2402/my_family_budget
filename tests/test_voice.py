import pytest
from unittest.mock import patch, MagicMock
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
