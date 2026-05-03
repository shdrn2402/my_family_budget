import pytest
from bot.services.llm import parse_natural_language

@pytest.mark.asyncio
async def test_parse_natural_language_russian():
    """Test LLM extraction with Russian text."""
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
async def test_parse_natural_language_english():
    """Test LLM extraction with English text."""
    text = "bought some groceries for 150.50 using my debit card"
    result = await parse_natural_language(text)
    
    assert len(result) == 1, "LLM should extract exactly 1 item"
    
    item = result[0]
    assert item['item_name'].lower() == 'groceries'
    assert item['amount'] == 150.5
    assert item['account_alias'].lower() in ['дебет', 'debit', 'bank', 'check']
