import logging
import psycopg
from psycopg.rows import dict_row
from bot.config import Config

logger = logging.getLogger(__name__)

async def get_db_connection() -> psycopg.AsyncConnection:
    """
    Create and return an async connection to the PostgreSQL database.
    Uses dict_row to return results as dictionaries instead of tuples.
    """
    return await psycopg.AsyncConnection.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        row_factory=dict_row,
        options="-c search_path=budget,public"
    )

async def check_user_exists(user_id: int, conn: psycopg.AsyncConnection | None = None) -> bool:
    """Check if a user exists in the database."""
    try:
        connection = conn or await get_db_connection()
        # If conn was provided, we don't manage its lifecycle here (no `async with connection`)
        # But for simplicity, we manage cursor
        async with connection.cursor() as cur:
            await cur.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
            result = await cur.fetchone()
            
        if conn is None:
            await connection.close()
            
        return result is not None
    except Exception as e:
        logger.error(f"Database error checking user {user_id}: {e}")
        return False

async def get_user_info(user_id: int, conn: psycopg.AsyncConnection | None = None) -> dict | None:
    """Get full user information including family_id and is_admin status."""
    result = None
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute("SELECT id, family_id, name, is_admin FROM users WHERE id = %s;", (user_id,))
            result = await cur.fetchone()
            
        if conn is None:
            await connection.close()
            
        return result
    except Exception as e:
        logger.error(f"Database error getting user info for {user_id}: {e}")
        return None

async def register_user(user_id: int, name: str, family_id: int = 1, is_admin: bool = False, conn: psycopg.AsyncConnection | None = None) -> bool:
    """
    Register a new user in the database.
    Defaults to family_id = 1 for the initial setup.
    """
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute(
                "INSERT INTO users (id, family_id, name, is_admin) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;",
                (user_id, family_id, name, is_admin)
            )
        await connection.commit()
        
        if conn is None:
            await connection.close()
            
        return True
    except Exception as e:
        logger.error(f"Database error registering user {user_id}: {e}")
        return False

async def get_recent_transactions(user_id: int, limit: int = 10, offset: int = 0, conn: psycopg.AsyncConnection | None = None) -> list:
    """
    Fetch transactions from the DB for a specific user with pagination support.
    """
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute(
                """
                SELECT 
                    t.id, 
                    t.description, 
                    t.amount, 
                    t.date, 
                    a.name as account_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                WHERE t.user_id = %s
                ORDER BY t.date DESC
                LIMIT %s OFFSET %s;
                """,
                (user_id, limit, offset)
            )
            result = await cur.fetchall()
            
        if conn is None:
            await connection.close()
            
        return result
    except Exception as e:
        logger.error(f"Database error fetching transactions for user {user_id}: {e}")
        return []

async def get_transactions_count(user_id: int, conn: psycopg.AsyncConnection | None = None) -> int:
    """Return total number of transactions for a user."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute("SELECT COUNT(*) as count FROM transactions WHERE user_id = %s;", (user_id,))
            result = await cur.fetchone()
            
        if conn is None:
            await connection.close()
            
        return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Database error counting transactions for user {user_id}: {e}")
        return 0
async def get_account_type(account_id: int, conn: psycopg.AsyncConnection | None = None) -> str | None:
    """Return the type of the account (e.g., 'card', 'cash')."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute("SELECT type FROM accounts WHERE id = %s;", (account_id,))
            result = await cur.fetchone()
            
        if conn is None:
            await connection.close()
            
        return result['type'] if result else None
    except Exception as e:
        logger.error(f"Database error getting account type for {account_id}: {e}")
        return None

async def save_transactions_bulk(user_id: int, transactions: list, conn: psycopg.AsyncConnection | None = None) -> int:
    """
    Save multiple transactions to the database.
    Skips duplicates based on external_id using ON CONFLICT DO NOTHING.
    Returns the number of successfully inserted rows.
    """
    try:
        connection = conn or await get_db_connection()
        inserted_count = 0
        
        async with connection.cursor() as cur:
            for tx in transactions:
                await cur.execute(
                    """
                    INSERT INTO transactions (user_id, account_id, category_id, amount, description, date, external_id, source_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (external_id) DO NOTHING;
                    """,
                    (
                        user_id,
                        tx['account_id'],
                        tx.get('category_id'), # Might be None
                        tx['amount'],
                        tx['description'],
                        tx['date'],
                        tx['external_id'],
                        'import_xls'
                    )
                )
                if cur.rowcount > 0:
                    inserted_count += 1
                    
        await connection.commit()
        if conn is None:
            await connection.close()
            
        return inserted_count
    except Exception as e:
        logger.error(f"Database error in bulk save for user {user_id}: {e}")
        return 0

async def sync_category_by_alias(description_pattern, category_id, user_id, conn=None):
    """
    1. Adds/updates an alias in item_aliases.
    2. Updates all transactions with matching description and NULL category.
    """
    connection = conn if conn else await get_db_connection()
    try:
        async with connection.cursor() as cur:
            # 1. Upsert into item_aliases
            await cur.execute("""
                INSERT INTO item_aliases (name, category_id, user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (name, user_id) DO UPDATE SET category_id = EXCLUDED.category_id;
            """, (description_pattern, category_id, user_id))
            
            # 2. Bulk update transactions
            await cur.execute("""
                UPDATE transactions
                SET category_id = %s
                WHERE user_id = %s 
                  AND category_id IS NULL
                  AND description ILIKE %s;
            """, (category_id, user_id, f"%{description_pattern}%"))
            
            updated_count = cur.rowcount
            await connection.commit()
            return updated_count
    finally:
        if conn is None:
            await connection.close()

async def execute_read_only_query(sql: str, params: tuple = None) -> list:
    """
    Executes a read-only SELECT query and returns the results.
    Safety: Explicitly checks for SELECT and prevents mutations.
    """
    clean_sql = sql.strip().upper()
    if not clean_sql.startswith("SELECT"):
        logger.warning(f"Blocked non-SELECT query: {sql}")
        return []

    # Basic protection against SQL injection and dangerous commands
    forbidden = ["UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "INSERT", "GRANT", "REVOKE"]
    if any(cmd in clean_sql for cmd in forbidden):
        logger.warning(f"Blocked dangerous query: {sql}")
        return []

    try:
        conn = await get_db_connection()
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            result = await cur.fetchall()
        await conn.close()
        return result
    except Exception as e:
        logger.error(f"SQL execution error: {e}\nQuery: {sql}")
        raise e

async def get_user_linked_account(user_id: int, conn: psycopg.AsyncConnection | None = None) -> dict | None:
    """Get the account currently linked to the user, if any."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute(
                "SELECT id, name, type FROM accounts WHERE owner_id = %s LIMIT 1;", 
                (user_id,)
            )
            result = await cur.fetchone()
        if conn is None:
            await connection.close()
        return result
    except Exception as e:
        logger.error(f"Error getting linked account for user {user_id}: {e}")
        return None

async def get_unlinked_accounts(family_id: int, conn: psycopg.AsyncConnection | None = None) -> list[dict]:
    """Get list of free (unlinked) card accounts for a family."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute(
                "SELECT id, name FROM accounts WHERE family_id = %s AND owner_id IS NULL AND type = 'card' ORDER BY id;", 
                (family_id,)
            )
            result = await cur.fetchall()
        if conn is None:
            await connection.close()
        return result
    except Exception as e:
        logger.error(f"Error getting unlinked accounts for family {family_id}: {e}")
        return []

async def link_user_to_account(user_id: int, account_id: int, conn: psycopg.AsyncConnection | None = None) -> bool:
    """Link user to specified account, with concurrency safety."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute("SELECT owner_id FROM accounts WHERE id = %s FOR UPDATE;", (account_id,))
            res = await cur.fetchone()
            if res and res['owner_id'] is not None:
                return False # Already claimed
                
            await cur.execute(
                "UPDATE accounts SET owner_id = %s WHERE id = %s;", 
                (user_id, account_id)
            )
        await connection.commit()
        if conn is None:
            await connection.close()
        return True
    except Exception as e:
        logger.error(f"Error linking user {user_id} to account {account_id}: {e}")
        return False
