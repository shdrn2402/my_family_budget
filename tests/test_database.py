import pytest
from bot.database import check_user_exists, register_user

@pytest.mark.asyncio
async def test_register_and_check_user():
    """Test user registration and checking existence."""
    test_user_id = 999999
    test_username = "test_user_999999"

    # Register the user
    success = await register_user(user_id=test_user_id, name=test_username)
    assert success is True, "Failed to register user"

    # Check if user exists
    exists = await check_user_exists(user_id=test_user_id)
    assert exists is True, "User should exist after registration"
