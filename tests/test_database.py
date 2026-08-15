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
        self.rowcount = 1
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        pass
        
    async def execute(self, query, params=None):
        self.execute_calls.append((query, params))
        
    async def fetchone(self):
        return {"exists": self.exists_val}

    async def fetchall(self):
        if self.exists_val:
            return [
                {"tablename": "users"},
                {"tablename": "accounts"},
                {"tablename": "account_aliases"},
                {"tablename": "categories"},
                {"tablename": "item_aliases"},
                {"tablename": "transactions"}
            ]
        return []

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
    """Test init_db when the database is already initialized (all tables exist)."""
    test_conn = MockConnection(exists_val=True)
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        await init_db()
        
    assert len(test_conn.cursor_obj.execute_calls) == 1
    assert "SELECT tablename FROM pg_tables" in test_conn.cursor_obj.execute_calls[0][0]


@pytest.mark.asyncio
async def test_init_db_restore_from_backup():
    """Test init_db when database is empty and a backup file is found."""
    test_conn = MockConnection(exists_val=False)
    
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"")
    mock_process.returncode = 0

    with patch("bot.database.get_db_connection", return_value=test_conn), \
         patch("os.path.exists", return_value=True), \
         patch("glob.glob", return_value=["/app/backups/db_backup_20260702_182743.sql"]), \
         patch("shutil.which", return_value="/usr/bin/psql"), \
         patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
         
        await init_db()
        
        # Verify psql was called to restore asynchronously
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        cmd = args
        assert "psql" in cmd
        assert "-v" in cmd
        assert "ON_ERROR_STOP=1" in cmd
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


@pytest.mark.asyncio
async def test_save_transactions_bulk_reconciliation():
    """Test that save_transactions_bulk reconciles with both pending and import_bit statuses."""
    from bot.database import save_transactions_bulk
    
    test_conn = MockConnection()
    # We mock fetchone to return a match indicating it found a transaction (e.g. from Bit)
    test_conn.cursor_obj.fetchone = AsyncMock(return_value={'id': 42, 'source_type': 'import_bit'})
    
    test_txs = [{
        'amount': -100.0,
        'date': '2026-05-15',
        'external_id': 'bank_123',
        'account_id': 1,
        'description': 'העברה בBIT',
        'category_id': None
    }]
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        inserted = await save_transactions_bulk(999, test_txs)
        
    assert inserted == 1
    # Check that SELECT checked for both pending and import_bit
    # The first query is now 'SELECT id, owner_id FROM accounts;'
    # The second query is the reconciliation check
    select_query = test_conn.cursor_obj.execute_calls[1][0]
    assert "(status = 'pending' OR source_type = ANY(%s))" in select_query, "Must search for specific target sources as well as pending"
    
    # Check that UPDATE statement updates external_id but DOES NOT overwrite category_id
    update_query = test_conn.cursor_obj.execute_calls[2][0]
    assert "category_id =" not in update_query, "Category ID must be preserved during reconciliation"
    assert "account_id =" not in update_query, "Account ID must be preserved from the Bit import"
    assert "description =" not in update_query, "Description must be preserved from the Bit import"

@pytest.mark.asyncio
async def test_sync_category_by_alias_composite():
    """Test that sync_category_by_alias handles composite aliases."""
    from bot.database import sync_category_by_alias
    
    test_conn = MockConnection()
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        await sync_category_by_alias("manicure + albina", 15, 999)
        
    # Check that it uses the exact composite string for the alias insert
    insert_query = test_conn.cursor_obj.execute_calls[0][0]
    insert_params = test_conn.cursor_obj.execute_calls[0][1]
    insert_params = test_conn.cursor_obj.execute_calls[0][1]
    assert "INSERT INTO item_aliases" in insert_query
    assert insert_params[0] == "manicure + albina", "Must insert the composite alias"

@pytest.mark.asyncio
async def test_save_transactions_bulk_preserves_comment_and_source_type():
    """Test that new transactions save the comment and source_type fields."""
    from bot.database import save_transactions_bulk
    
    test_conn = MockConnection()
    # Return None so it doesn't match and inserts a new row
    test_conn.cursor_obj.fetchone = AsyncMock(return_value=None)
    
    test_txs = [{
        'amount': -100.0,
        'date': '2026-05-15',
        'external_id': 'bit_123',
        'account_id': 1,
        'description': 'Bit Transfer',
        'comment': 'Test Person',
        'source_type': 'import_bit'
    }]
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        inserted = await save_transactions_bulk(999, test_txs)
        
    assert inserted == 1
    
    # Check that INSERT includes comment and correct source_type
    insert_query = test_conn.cursor_obj.execute_calls[2][0]
    insert_params = test_conn.cursor_obj.execute_calls[2][1]
    
    assert "INSERT INTO transactions" in insert_query
    assert "comment" in insert_query
    assert "Test Person" in insert_params
    assert "import_bit" in insert_params

@pytest.mark.asyncio
async def test_save_transactions_bulk_merges_bit_and_isracard():
    """Test that Bit and Isracard overlap is correctly handled without duplication."""
    from bot.database import save_transactions_bulk
    
    test_conn = MockConnection()
    
    # Simulate DB having an Isracard record (import_xls)
    test_conn.cursor_obj.fetchone = AsyncMock(return_value={
        'id': 100,
        'source_type': 'import_xls'
    })
    
    test_txs_bit = [{
        'amount': -300.0,
        'date': '2026-07-05',
        'external_id': 'bit_123',
        'account_id': 1,
        'description': 'Bit Transfer',
        'comment': 'Test Person',
        'source_type': 'import_bit'
    }]
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        inserted = await save_transactions_bulk(999, test_txs_bit)
        
    assert inserted == 1
    
    # Check that UPDATE is executed, appending the comment but NOT overwriting external_id
    update_query = test_conn.cursor_obj.execute_calls[2][0]
    update_params = test_conn.cursor_obj.execute_calls[2][1]
    
    assert "UPDATE transactions" in update_query
    assert "external_id =" not in update_query, "Must not overwrite Isracard external_id"
    assert "comment = CASE" in update_query, "Must append comment"
    assert "Test Person" in update_params

@pytest.mark.asyncio
async def test_get_latest_import_date():
    """Test that get_latest_import_date returns the max date for a source."""
    from bot.database import get_latest_import_date
    import datetime
    
    test_conn = MockConnection()
    expected_date = datetime.date(2026, 7, 5)
    test_conn.cursor_obj.fetchone = AsyncMock(return_value={'max': expected_date})
    
    with patch("bot.database.get_db_connection", return_value=test_conn):
        date = await get_latest_import_date('import_bit')
        
    assert date == expected_date
    
    select_query = test_conn.cursor_obj.execute_calls[0][0]
    select_params = test_conn.cursor_obj.execute_calls[0][1]
    
    assert "SELECT MAX(date)" in select_query
    assert "import_bit" in select_params
