import pytest
from unittest.mock import AsyncMock, patch
from bot.services.expense import process_expense_text

@pytest.mark.asyncio
@patch('bot.services.expense.parse_natural_language')
@patch('bot.services.expense.resolve_account')
@patch('bot.services.expense.resolve_category_from_alias')
async def test_process_expense_text_fast_path(mock_resolve_category, mock_resolve_account, mock_llm):
    """Test that correctly formatted text uses the fast parser and skips LLM."""
    mock_conn = AsyncMock()
    mock_resolve_account.return_value = 1
    mock_resolve_category.return_value = 2
    
    text = "кола нал 5"
    results = await process_expense_text(text, mock_conn)
    
    # Fast parser should succeed
    assert len(results) == 1
    assert 'error' not in results[0]
    assert results[0]['amount'] == 5.0
    
    # LLM should NEVER be called
    mock_llm.assert_not_called()

@pytest.mark.asyncio
@patch('bot.services.expense.parse_natural_language')
@patch('bot.services.expense.resolve_account')
@patch('bot.services.expense.resolve_category_from_alias')
async def test_process_expense_text_llm_fallback(mock_resolve_category, mock_resolve_account, mock_llm):
    """Test that badly formatted text falls back to the LLM."""
    mock_conn = AsyncMock()
    
    # Mock LLM returning structured data
    mock_llm.return_value = [{'item_name': 'кофе', 'amount': 500.0, 'account_alias': 'нал'}]
    mock_resolve_account.return_value = 3
    mock_resolve_category.return_value = None
    
    text = "вчера отдал 500 за кофе налом"
    results = await process_expense_text(text, mock_conn)
    
    # Fast parser fails, LLM succeeds
    assert len(results) == 1
    mock_llm.assert_called_once_with(text)

@pytest.mark.asyncio
async def test_process_expense_text_skips_llm_for_all_short_messages():
    """Test that all messages with < 3 words skip the LLM to save tokens."""
    from bot.services.expense import process_expense_text
    mock_conn = AsyncMock()
    
    with patch('bot.services.expense.parse_natural_language') as mock_llm:
        # 1 word
        await process_expense_text("кофе", mock_conn)
        # 2 words with number
        await process_expense_text("кола 50", mock_conn)
        # 2 words without number
        await process_expense_text("купил кофе", mock_conn)
        
        # LLM should NEVER be called for messages with less than 3 words
        mock_llm.assert_not_called()

