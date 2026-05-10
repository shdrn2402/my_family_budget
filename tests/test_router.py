import pytest
from unittest.mock import patch, AsyncMock
from bot.services.router import classify_intent

def mock_gemini_response(intent: str):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    # json() is synchronous in httpx
    mock_resp.json = lambda: {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": intent}]
                }
            }
        ]
    }
    return mock_resp

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_classify_intent_expense(mock_post):
    mock_post.return_value = mock_gemini_response("EXPENSE")
    
    assert await classify_intent("хлеб 100") == "EXPENSE"
    assert await classify_intent("купил бензин за 200") == "EXPENSE"
    assert await classify_intent("got salary 5000") == "EXPENSE"

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_classify_intent_analytics(mock_post):
    mock_post.return_value = mock_gemini_response("ANALYTICS")
    
    assert await classify_intent("сколько я потратил на еду?") == "ANALYTICS"
    assert await classify_intent("сравни расходы по месяцам") == "ANALYTICS"
    assert await classify_intent("структура трат за год") == "ANALYTICS"
    assert await classify_intent("spending on car") == "ANALYTICS"

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_classify_intent_unknown(mock_post):
    mock_post.return_value = mock_gemini_response("UNKNOWN")
    
    assert await classify_intent("Привет, как дела?") == "UNKNOWN"

