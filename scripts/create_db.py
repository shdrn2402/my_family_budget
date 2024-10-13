import psycopg2
import logging
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(filename='logs/app.log',
                    level=logging.INFO,
                    encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Получение значений переменных окружения
DBNAME = os.getenv('DBNAME')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')


def create_database(db_name):
    """
    Создает базу данных, если она еще не существует.

    Args:
        db_name: Имя создаваемой базы данных.
    """

    # Подключение к базе данных postgres для создания новой базы данных
    conn = psycopg2.connect(
        database="postgres",
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

    # Отключение транзакционного блока
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute(f"CREATE DATABASE {db_name}")
        logger.info(f"База данных {db_name} создана успешно.")
    except psycopg2.errors.DuplicateDatabase:
        logger.info(f"База данных {db_name} уже существует.")
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных {db_name}: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def create_table(conn, table_name, sql_query):
    """
    Проверяет наличие таблицы и создает ее, если она не существует.

    Args:
        conn: Соединение с базой данных.
        table_name: Имя создаваемой таблицы.
        sql_query: SQL-запрос для создания таблицы.
    """

    cursor = conn.cursor()

    try:
        # Проверка существования таблицы
        cursor.execute(f"""SELECT EXISTS (SELECT FROM information_schema.tables
                       WHERE table_name = '{table_name}');""")
        exists = cursor.fetchone()[0]

        if exists:
            logger.info(f"Таблица {table_name} уже существует.")
        else:
            # Установка схемы по умолчанию
            cursor.execute("SET search_path TO budget;")

            # Создание таблицы
            cursor.execute(sql_query)
            conn.commit()  # Сохранение изменений в базе данных
            logger.info(f"Таблица {table_name} создана успешно.")
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы {table_name}: {str(e)}")
    finally:
        cursor.close()


def main():
    # Создаем базу данных, если она не существует
    create_database(DBNAME)

    # Подключаемся к базе данных
    conn = psycopg2.connect(
        database=DBNAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

    # SQL-запросы для создания таблиц
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        user_name VARCHAR(50) NOT NULL,
        family_id INTEGER NOT NULL,
        language VARCHAR(10) NOT NULL
    );
    """

    create_roles_table = """
    CREATE TABLE IF NOT EXISTS roles (
        id SERIAL PRIMARY KEY,
        role_name VARCHAR(50) NOT NULL
    );
    """

    # Создаем таблицы
    create_table(conn, "users", create_users_table)
    create_table(conn, "roles", create_roles_table)

    conn.close()


if __name__ == "__main__":
    main()
