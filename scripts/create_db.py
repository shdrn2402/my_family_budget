import psycopg
import logging
from dotenv import load_dotenv
import os
import re

# Logging setup
logging.basicConfig(filename="logs/app.log",
                    level=logging.INFO,
                    encoding="utf-8",
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Retrieve environment variables
ROOT_DBNAME = os.getenv("ROOT_DBNAME")
DBNAMETOCREATE = os.getenv("NEW_DBNAME")
ROOT_USER = os.getenv("ROOT_USER")
ROOT_PASSWORD = os.getenv("ROOT_PASSWORD")
MAIN_USER = os.getenv("MAIN_USER")
MAIN_USER_PASSWORD = os.getenv("MAIN_USER_PASSWORD")
COMMON_USER = os.getenv("COMMON_USER")
COMMON_USER_PASSWORD = os.getenv("COMMON_USER_PASSWORD")
READ_ONLY_USER = os.getenv("READ_ONLY_USER")
READ_ONLY_USER_PASSWORD = os.getenv("READ_ONLY_USER_PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")


def create_database(root_db_name, root_user, root_password, host, port,
                    db_name_to_create):
    """
    Creates a new database if it does not already exist.

    Args:
        root_db_name: The name of the default system database
        used for administrative tasks.
        root_user: The superuser's username to connect to the database.
        root_password: The superuser's password for the connection.
        host: The database server's host.
        port: The port number where the PostgreSQL server is running.
        db_name_to_create: The name of the database to be created.
    """

    logger.info("Creating database %s...", db_name_to_create)

    # Check the database name
    if re.match(r"^[a-zA-Z0-9_]+$", db_name_to_create):
        # Connect to an existing database
        with psycopg.connect(
            dbname=root_db_name,
            user=root_user,
            password=root_password,
            host=host,
            port=port
        ) as conn:
            # Set autocommit
            conn.autocommit = True
            # Open a cursor to perform database operations
            with conn.cursor() as cursor:
                # Execute a command: this creates a new database
                try:
                    cursor.execute(f"CREATE DATABASE {db_name_to_create}")
                    logger.info(
                        "Database %s created successfully.",
                        db_name_to_create
                    )
                except psycopg.errors.DuplicateDatabase:
                    logger.info(
                        "Database %s already exists.",
                        db_name_to_create
                    )
                except psycopg.Error as e:
                    # Log all other errors related to PostgreSQL
                    logger.error(
                        "PostgreSQL error while creating the database %s: %s",
                        db_name_to_create, str(e)
                    )
                    # Raise the same exception to stop the script
                    raise
                except Exception as e:
                    # Log any unexpected errors not related to PostgreSQL
                    logger.error("Unexpected error: %s", str(e))
                    # Raise the same exception to stop the script
                    raise
    else:
        logger.error("Invalid database name: %s", db_name_to_create)
        raise ValueError(f"Invalid database name: {db_name_to_create}")


# def create_table(conn, table_name, sql_query):
#     """
#     Проверяет наличие таблицы и создает ее, если она не существует.

#     Args:
#         conn: Соединение с базой данных.
#         table_name: Имя создаваемой таблицы.
#         sql_query: SQL-запрос для создания таблицы.
#     """

#     cursor = conn.cursor()

#     try:
#         # Проверка существования таблицы
#         cursor.execute(f"""SELECT EXISTS (SELECT FROM information_schema.tables
#                        WHERE table_name = '{table_name}');""")
#         exists = cursor.fetchone()[0]

#         if exists:
#             logger.info(f"Таблица {table_name} уже существует.")
#         else:
#             # Установка схемы по умолчанию
#             cursor.execute("SET search_path TO budget;")

#             # Создание таблицы
#             cursor.execute(sql_query)
#             conn.commit()  # Сохранение изменений в базе данных
#             logger.info(f"Таблица {table_name} создана успешно.")
#     except Exception as e:
#         logger.error(f"Ошибка при создании таблицы {table_name}: {str(e)}")
#     finally:
#         cursor.close()


def main():
    # Создаем базу данных, если она не существует
    create_database(root_db_name=ROOT_DBNAME,
                    root_user=ROOT_USER,
                    root_password=ROOT_PASSWORD,
                    host=HOST,
                    port=PORT,
                    db_name_to_create=DBNAMETOCREATE)

    # Подключаемся к базе данных
    # conn = psycopg2.connect(
    #     database=DBNAME,
    #     user=USER,
    #     password=PASSWORD,
    #     host=HOST,
    #     port=PORT
    # )

    # # SQL-запросы для создания таблиц
    # create_users_table = """
    # CREATE TABLE IF NOT EXISTS users (
    #     tg_id INTEGER PRIMARY KEY,
    #     user_name VARCHAR(50) NOT NULL,
    #     family_id INTEGER NOT NULL,
    #     language VARCHAR(10) NOT NULL
    # );
    # """

    # create_roles_table = """
    # CREATE TABLE IF NOT EXISTS roles (
    #     id SERIAL PRIMARY KEY,
    #     role_name VARCHAR(50) NOT NULL
    # );
    # """

    # # Создаем таблицы
    # create_table(conn, "users", create_users_table)
    # create_table(conn, "roles", create_roles_table)

    # conn.close()


if __name__ == "__main__":
    main()
