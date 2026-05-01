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
    conn_info: str = (
        f"dbname={Config.DB_NAME} user={Config.DB_USER} "
        f"password={Config.DB_PASSWORD} host={Config.DB_HOST} port={Config.DB_PORT}"
    )
    return await psycopg.AsyncConnection.connect(conn_info, row_factory=dict_row)

async def check_user_exists(user_id: int) -> bool:
    """Check if a user exists in the database."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
                result = await cur.fetchone()
                return result is not None
    except Exception as e:
        logger.error(f"Database error checking user {user_id}: {e}")
        return False

async def register_user(user_id: int, name: str, family_id: int = 1) -> bool:
    """
    Register a new user in the database.
    Defaults to family_id = 1 for the initial setup.
    """
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (id, family_id, name) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING;",
                    (user_id, family_id, name)
                )
            await conn.commit()
            return True
    except Exception as e:
        logger.error(f"Database error registering user {user_id}: {e}")
        return False
