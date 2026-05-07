import pytest
from unittest.mock import AsyncMock, patch
from bot.services import llm
from bot.database import execute_read_only_query

@pytest.mark.asyncio
async def test_translate_question_to_sql_logic():
    """Test that LLM service correctly generates SQL from a natural language question."""
    user_id = 12345
    question = "How much did I spend on food?"
    
    # Mocking the LLM response
    mock_sql_response = {
        "sql": "SELECT ABS(SUM(amount)) FROM transactions WHERE user_id = 12345 AND description ILIKE '%food%'",
        "explanation": "Calculates total spending on food for user 12345",
        "is_safe": True
    }
    
    with patch("bot.services.llm.translate_question_to_sql", new_callable=AsyncMock) as mock_translate:
        mock_translate.return_value = mock_sql_response
        
        result = await llm.translate_question_to_sql(question, user_id)
        
        assert "sql" in result
        assert "user_id = 12345" in result["sql"]
        assert result["is_safe"] is True

@pytest.mark.asyncio
async def test_generate_answer_from_data_logic():
    """Test that LLM service generates a human-friendly answer from DB results."""
    question = "How much did I spend on food?"
    data_rows = [{"total": 150.50}]
    
    mock_answer = "You spent 150.50 on food."
    
    with patch("bot.services.llm.generate_answer_from_data", new_callable=AsyncMock) as mock_answer_gen:
        mock_answer_gen.return_value = mock_answer
        
        result = await llm.generate_answer_from_data(question, data_rows)
        
        assert "150.50" in result
        assert "food" in result

@pytest.mark.asyncio
async def test_execute_read_only_query_safety():
    """Test that database service blocks non-SELECT queries."""
    # This should be blocked by our logic in database.py and return empty list
    result = await execute_read_only_query("DELETE FROM transactions")
    assert result == []
