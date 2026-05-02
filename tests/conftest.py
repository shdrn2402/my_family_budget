import pytest
from unittest.mock import patch

class FakeCursor:
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        pass
        
    async def execute(self, query, params=None):
        pass
        
    async def fetchone(self):
        return {"id": 999999}

class FakeConnection:
    def cursor(self):
        return FakeCursor()
        
    async def commit(self):
        pass
        
    async def close(self):
        pass

@pytest.fixture(autouse=True)
def mock_db_connection():
    """
    Mock the database connection for testing.
    This ensures we don't hit the production DB and tests run fast.
    """
    with patch("bot.database.get_db_connection") as mock_get_conn:
        # get_db_connection is an async function, so its return_value should be awaitable
        # In Python 3.8+, AsyncMock is standard, but since we are patching an async function,
        # we can just make it return a FakeConnection when awaited.
        from unittest.mock import AsyncMock
        mock_get_conn_async = AsyncMock()
        mock_get_conn_async.return_value = FakeConnection()
        
        # apply patch
        with patch("bot.database.get_db_connection", new=mock_get_conn_async):
            yield
