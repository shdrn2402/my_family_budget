import pytest
from bot.services.router import classify_intent

@pytest.mark.asyncio
async def test_classify_intent_expense():
    # Regular expenses
    assert await classify_intent("хлеб 100") == "EXPENSE"
    assert await classify_intent("купил бензин за 200") == "EXPENSE"
    assert await classify_intent("got salary 5000") == "EXPENSE"

@pytest.mark.asyncio
async def test_classify_intent_analytics():
    # Analytical questions
    assert await classify_intent("сколько я потратил на еду?") == "ANALYTICS"
    assert await classify_intent("сравни расходы по месяцам") == "ANALYTICS"
    assert await classify_intent("структура трат за год") == "ANALYTICS"
    assert await classify_intent("spending on car") == "ANALYTICS"

@pytest.mark.asyncio
async def test_classify_intent_unknown():
    # Grettings or random stuff should probably be EXPENSE or UNKNOWN
    # depending on how we want the bot to behave.
    # Currently UNKNOWN defaults to expense processing.
    assert await classify_intent("Привет, как дела?") == "UNKNOWN"
