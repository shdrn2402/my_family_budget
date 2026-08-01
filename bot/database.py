import logging
import psycopg
from psycopg.rows import dict_row
import asyncio
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
    """Get full user information including is_admin status."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute("SELECT id, name, is_admin FROM users WHERE id = %s;", (user_id,))
            result = await cur.fetchone()
            
        if conn is None:
            await connection.close()
            
        return result
    except Exception as e:
        logger.error(f"Database error getting user info for {user_id}: {e}")
        return None

async def register_user(user_id: int, name: str, is_admin: bool = False, conn: psycopg.AsyncConnection | None = None) -> bool:
    """
    Register a new user in the database.
    """
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute(
                "INSERT INTO users (id, name, is_admin) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING;",
                (user_id, name, is_admin)
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
        
        # 1. Fetch all accounts and their owner_ids in one query
        account_owners = {}
        async with connection.cursor() as cur:
            await cur.execute("SELECT id, owner_id FROM accounts;")
            accounts_rows = await cur.fetchall()
            for row in accounts_rows:
                account_owners[row['id']] = row['owner_id']
        
        async with connection.cursor() as cur:
            for tx in transactions:
                # Try to find a matching pending manual transaction OR an import_bit transaction (ignoring account_id)
                await cur.execute(
                    """
                    SELECT id, source_type FROM transactions 
                    WHERE amount = %s 
                      AND (status = 'pending' OR source_type IN ('import_bit', 'import_xls'))
                      AND date BETWEEN %s::date - INTERVAL '3 days' AND %s::date + INTERVAL '3 days'
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED;
                    """,
                    (tx['amount'], tx['date'], tx['date'])
                )
                match = await cur.fetchone()

                if match:
                    if tx.get('source_type') == 'import_bit':
                        # We are importing Bit. It matched an existing Isracard or Bit record.
                        # We DO NOT want to overwrite an Isracard external_id with a Bit external_id.
                        # We will only append the Bit comment if it's missing.
                        await cur.execute(
                            """
                            UPDATE transactions 
                            SET comment = CASE 
                                            WHEN comment IS NOT NULL AND comment != '' AND comment NOT LIKE '%' || %s || '%' THEN comment || ', ' || %s 
                                            WHEN comment IS NULL OR comment = '' THEN %s
                                            ELSE comment 
                                          END
                            WHERE id = %s;
                            """,
                            (tx.get('comment', ''), tx.get('comment', ''), tx.get('comment', ''), match['id'])
                        )
                        inserted_count += 1
                        
                    elif match['source_type'] in ('import_bit', 'import_xls'):
                        # We are importing Isracard (xls). It matched an existing Bit (or another xls).
                        # Isracard is the source of truth for the bank statement, so we overwrite external_id and change source_type to import_xls.
                        await cur.execute(
                            """
                            UPDATE transactions 
                            SET external_id = %s,
                                source_type = 'import_xls',
                                comment = CASE 
                                            WHEN comment IS NOT NULL AND comment != '' AND comment NOT LIKE '%' || %s || '%' THEN comment || ', ' || %s 
                                            WHEN comment IS NULL OR comment = '' THEN %s
                                            ELSE comment 
                                          END
                            WHERE id = %s;
                            """,
                            (tx['external_id'], tx['description'], tx['description'], tx['description'], match['id'])
                        )
                        inserted_count += 1
                        
                    else:
                        # We are importing Isracard (xls) or Bit. It matched a manual pending record! Update with details.
                        await cur.execute(
                            """
                            UPDATE transactions 
                            SET status = 'confirmed', 
                                external_id = %s, 
                                date = %s, 
                                source_type = %s,
                                account_id = %s,
                                comment = CASE 
                                            WHEN comment IS NOT NULL AND comment != '' THEN description || ', ' || comment 
                                            ELSE description 
                                          END,
                                description = %s
                            WHERE id = %s;
                            """,
                            (tx['external_id'], tx['date'], tx.get('source_type', 'import_xls'), tx['account_id'], tx['description'], match['id'])
                        )
                        inserted_count += 1
                else:
                    # Resolve user_id based on account owner
                    tx_user_id = account_owners.get(tx['account_id'])
                    if tx_user_id is None:
                        tx_user_id = user_id
                        
                    # No match, insert as new
                    await cur.execute(
                        """
                        INSERT INTO transactions (user_id, account_id, category_id, amount, description, comment, date, external_id, source_type, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'confirmed')
                        ON CONFLICT (external_id) DO NOTHING;
                        """,
                        (
                            tx_user_id,
                            tx['account_id'],
                            tx.get('category_id'),
                            tx['amount'],
                            tx['description'],
                            tx.get('comment'),
                            tx['date'],
                            tx['external_id'],
                            tx.get('source_type', 'import_xls')
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

async def sync_category_by_alias(alias_name, category_id, user_id, conn=None):
    """
    1. Adds/updates an alias in item_aliases (using composite alias_name).
    2. Updates all transactions with matching description+comment and NULL category.
    """
    connection = conn if conn else await get_db_connection()
    try:
        async with connection.cursor() as cur:
            # 1. Upsert into item_aliases
            await cur.execute("""
                INSERT INTO item_aliases (name, category_id)
                VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET category_id = EXCLUDED.category_id;
            """, (alias_name.lower().strip(), category_id))
            
            # 2. Bulk update transactions
            # We match where the composite of description and comment ILIKE the alias_name
            await cur.execute("""
                UPDATE transactions
                SET category_id = %s
                WHERE user_id = %s 
                  AND category_id IS NULL
                  AND (
                      description ILIKE %s OR 
                      (description || ' ' || COALESCE(comment, '')) ILIKE %s
                  );
            """, (category_id, user_id, f"%{alias_name}%", f"%{alias_name}%"))
            
            updated_count = cur.rowcount
            await connection.commit()
            return updated_count
    finally:
        if conn is None:
            await connection.close()

async def get_all_item_aliases(conn: psycopg.AsyncConnection | None = None) -> dict[str, int]:
    """
    Fetches all item aliases from the database and returns them as a dictionary mapping name -> category_id.
    """
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute("SELECT name, category_id FROM item_aliases;")
            result = await cur.fetchall()
            
        if conn is None:
            await connection.close()
            
        # Ensure keys are upper case for robust matching if needed, 
        # though clean_business_name already makes them upper.
        return {row['name']: row['category_id'] for row in result}
    except Exception as e:
        logger.error(f"Database error fetching all item aliases: {e}")
        return {}


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

async def get_unlinked_accounts(conn: psycopg.AsyncConnection | None = None) -> list[dict]:
    """Get accounts that haven't been linked to a user yet."""
    try:
        connection = conn or await get_db_connection()
        async with connection.cursor() as cur:
            await cur.execute(
                "SELECT id, name FROM accounts WHERE owner_id IS NULL AND type = 'card' ORDER BY id;"
            )
            result = await cur.fetchall()
        if conn is None:
            await connection.close()
        return result
    except Exception as e:
        logger.error(f"Error getting unlinked accounts: {e}")
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

async def init_db() -> None:
    """
    Initialize the database structure and seed data if it's empty.
    Includes a retry loop to wait for Postgres to become ready.
    """
    max_retries = 10
    retry_delay = 2
    conn = None

    for attempt in range(1, max_retries + 1):
        try:
            conn = await get_db_connection()
            break
        except Exception as e:
            logger.info(f"Waiting for database... (attempt {attempt}/{max_retries})")
            await asyncio.sleep(retry_delay)

    if not conn:
        logger.error("Failed to connect to the database after multiple retries.")
        return

    try:
        async with conn.cursor() as cur:
            # Check if all required tables exist in schema budget
            required_tables = {"users", "accounts", "account_aliases", "categories", "item_aliases", "transactions"}
            await cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'budget';"
            )
            res = await cur.fetchall()
            existing_tables = {row['tablename'] for row in res} if res else set()
            db_initialized = required_tables.issubset(existing_tables)

            if not db_initialized:
                # Close the connection to release locks before restore
                await conn.close()
                conn = None

                import os
                import glob
                import shutil

                # Find the latest backup
                backup_dirs = ["/app/backups", "backups", "../backups"]
                existing_dirs = [d for d in backup_dirs if os.path.exists(d)]
                
                backup_files = []
                for d in existing_dirs:
                    backup_files.extend(glob.glob(os.path.join(d, "db_backup_*.sql")))

                latest_backup = None
                if backup_files:
                    latest_backup = sorted(backup_files)[-1]

                # Pre-check if psql exists in the system
                psql_path = shutil.which("psql")

                if latest_backup and psql_path:
                    logger.info(f"Database structure is incomplete. Latest backup found: {latest_backup}. Preparing restore...")
                    
                    # Drop schema if exists to ensure clean restore
                    try:
                        conn_temp = await get_db_connection()
                        async with conn_temp.cursor() as cur_temp:
                            await cur_temp.execute("DROP SCHEMA IF EXISTS budget CASCADE;")
                            await conn_temp.commit()
                        await conn_temp.close()
                    except Exception as drop_err:
                        logger.warning(f"Failed to drop budget schema before restore: {drop_err}")

                    try:
                        env = os.environ.copy()
                        if Config.DB_PASSWORD:
                            env["PGPASSWORD"] = Config.DB_PASSWORD
                            
                        cmd = [
                            "psql",
                            "-v", "ON_ERROR_STOP=1",
                            "-h", Config.DB_HOST,
                            "-p", str(Config.DB_PORT),
                            "-U", Config.DB_USER,
                            "-d", Config.DB_NAME,
                            "-f", latest_backup
                        ]
                        
                        logger.info("Restoring database from backup using psql asynchronously...")
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            env=env,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode != 0:
                            error_msg = stderr.decode('utf-8', errors='replace')
                            logger.error(f"psql restore failed with return code {process.returncode}: {error_msg}")
                            raise Exception(error_msg)
                        
                        logger.info("Database successfully restored from backup.")
                        return
                    except Exception as restore_err:
                        logger.error(f"Failed to restore from backup: {restore_err}. Falling back to default initialization.")
                elif latest_backup and not psql_path:
                    logger.warning("Latest backup is available, but 'psql' client was not found on the system. Falling back to default initialization.")

                # Fallback to schema and seed data
                logger.info("Running schema initialization...")
                conn = await get_db_connection()
                async with conn.cursor() as cur:
                    with open("scripts/schema.sql", "r", encoding="utf-8") as f:
                        await cur.execute(f.read())
                    
                    try:
                        with open("scripts/seed_data.sql", "r", encoding="utf-8") as f:
                            await cur.execute(f.read())
                        logger.info("Database seeded successfully.")
                    except FileNotFoundError:
                        logger.warning("scripts/seed_data.sql not found, skipping seed.")
                        
                    await conn.commit()
                logger.info("Database initialization complete.")
            else:
                logger.info("Database already initialized, skipping.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    finally:
        if conn:
            await conn.close()

