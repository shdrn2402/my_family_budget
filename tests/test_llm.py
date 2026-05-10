import pytest
import json
from unittest.mock import patch, AsyncMock
from bot.services.llm import parse_natural_language

def mock_gemini_json_response(json_str: str):
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = lambda: {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json_str}]
                }
            }
        ]
    }
    return mock_resp

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_parse_natural_language_russian(mock_post):
    """Test LLM extraction with Russian text."""
    mock_resp_json = json.dumps({"items": [
        {"item_name": "кофе", "amount": 500.0, "account_alias": "нал"},
        {"item_name": "бензин", "amount": 2000.0, "account_alias": "кредитка"}
    ]})
    mock_post.return_value = mock_gemini_json_response(mock_resp_json)
    
    text = "вчера отдал 500 за кофе налом и 2к за бензин с кредитки"
    result = await parse_natural_language(text)
    
    assert len(result) == 2, "LLM should extract exactly 2 items"
    
    coffee_item = next(item for item in result if item['item_name'].lower() == 'кофе')
    assert coffee_item['amount'] == 500.0
    assert coffee_item['account_alias'].lower() in ['нал', 'наличные', 'cash']
    
    gas_item = next(item for item in result if item['item_name'].lower() == 'бензин')
    assert gas_item['amount'] == 2000.0
    assert gas_item['account_alias'].lower() in ['кредит', 'кредитка', 'card']

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_parse_natural_language_english(mock_post):
    """Test LLM extraction with English text."""
    mock_resp_json = json.dumps({"items": [
        {"item_name": "groceries", "amount": 150.5, "account_alias": "debit"}
    ]})
    mock_post.return_value = mock_gemini_json_response(mock_resp_json)

    
    text = "bought some groceries for 150.50 using my debit card"
    result = await parse_natural_language(text)
    
    assert len(result) == 1, "LLM should extract exactly 1 item"
    
    item = result[0]
    assert item['item_name'].lower() == 'groceries'
    assert item['amount'] == 150.5
    assert item['account_alias'].lower() in ['дебет', 'debit', 'bank', 'check']

