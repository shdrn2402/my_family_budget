import pytest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from bot.database import check_user_exists, register_user, init_db

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


class MockCursor:
    def __init__(self, exists_val=False):
        self.exists_val = exists_val
        self.execute_calls = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        pass
        
    async def execute(self, query, params=None):
        self.execute_calls.append((query, params))
        
    async def fetchone(self):
        return {"exists": self.exists_val}

class MockConnection:
    def __init__(self, exists_val=False):
        self.cursor_obj = MockCursor(exists_val)
        self.commit_called = False
        self.close_called = False
        
    def cursor(self):
        return self.cursor_obj
        
    async def commit(self):
        self.commit_called = True
        
    async def close(self):
        self.close_called = True


@pytest.mark.asyncio
async def test_init_db_already_initialized():
    """Test init_db when the database is already initialized (users table exists)."""
    test_conn = MockConnection(exists_val=True)
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        await init_db()
        
    assert len(test_conn.cursor_obj.execute_calls) == 1
    assert "SELECT EXISTS" in test_conn.cursor_obj.execute_calls[0][0]


@pytest.mark.asyncio
async def test_init_db_restore_from_backup():
    """Test init_db when database is empty and a backup file is found."""
    test_conn = MockConnection(exists_val=False)
    
    with patch("bot.database.get_db_connection", return_value=test_conn), \
         patch("os.path.exists", return_value=True), \
         patch("glob.glob", return_value=["/app/backups/db_backup_20260702_182743.sql"]), \
         patch("subprocess.run") as mock_run:
         
        mock_run.return_value = MagicMock(returncode=0)
        
        await init_db()
        
        # Verify psql was called to restore
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = args[0]
        assert "psql" in cmd
        assert "/app/backups/db_backup_20260702_182743.sql" in cmd


@pytest.mark.asyncio
async def test_init_db_fallback_to_schema():
    """Test init_db when database is empty and no backups are found."""
    test_conn = MockConnection(exists_val=False)
    
    with patch("bot.database.get_db_connection", return_value=test_conn), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open(read_data="SELECT 1;")) as mock_file:
         
        await init_db()
        
        # Verify schema.sql and seed_data.sql were opened
        assert mock_file.call_count >= 2


