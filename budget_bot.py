import logging
import os.path
import re
import subprocess

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

import mylib

load_dotenv()

data_folder = 'data/'
os.makedirs(data_folder, exist_ok=True)
data_path = os.path.join(data_folder, 'budget.csv')

log_folder = 'logs/'
os.makedirs(log_folder, exist_ok=True)
log_path = os.path.join(log_folder, 'logs.log')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=log_path,
    encoding='utf-8',
    level=logging.WARNING)


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DBNAME = os.environ.get('DBNAME')
USER = os.environ.get('USER')
PASSWORD = os.environ.get('PASSWORD')
PORT = os.environ.get('PORT')
HOST = os.environ.get('HOST')


def start_dashboard():
    print('Dashboard started...')
    subprocess.Popen(['python', 'dashboard.py'])


# def get_query_list(query_str: str) -> list:
#     if ',' in query_str:
#         query_list = query_str.split(',')
#     else:
#         query_list = [query_str]
#     return list(map(str.strip, query_list))


async def telegram_help_text(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message to the user."""
    user_first_name = (
        update.effective_user.first_name
        if update.effective_user
        else 'Added from Telegram'
    )

    text = f'''И так, {user_first_name},
На данный момент доступен только один вариант ввода комманд.
Для конкретной таблицы содержащей поля:
    - Наименование траты;
    - Источник траты (нал, карта, чек);
    - Сумма траты;
    - Дата траты.
Для ввода используется следующий формат:
[наименование] [источник] [сумма]
Если трат несколько, то нужно использовать запятую между каждым блоком.
Если наименование составное, например, "сыр колбаса вода",
то запятая не ставится!
Пример:
сыр колбаса вода карта 1000, овощи нал 800
Результат:
Наименование: Сыр колбаса вода
Источник: Карта
Сумма: 1000
Наименование: Овощи
Источник: Наличные
Сумма: 800
'''
    await update.message.reply_text(text)


async def telegram_start_text(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome messages to the user."""

    if update.effective_user:
        if update.effective_user.first_name:
            user_first_name = update.effective_user.first_name
        elif update.effective_user.username:
            user_first_name = update.effective_user.username
        else:
            user_first_name = 'Added from Telegram'
    else:
        user_first_name = 'Added from Telegram'

    text = f'''Привет, {user_first_name},
Это бот для ведения сейного бюджета с помощью telegram.
В данный момент это закрытый бот.
Функциональность ограничена для тестирования.
Используй /help для получения списка команд.'''

    await update.message.reply_text(text)


def check_update_keys(update: Update, required_keys: list) -> dict:
    """
    Checks if the specified keys are present in the update object and retrieves their values.

    :param update: The update object to check.
    :param required_keys: A list of required keys to check for.
    :return: A dictionary with keys and their values or None if not present.
    """
    key_values = {}

    for key in required_keys:
        try:
            # Пробуем получить значение по ключу из объекта update
            key_values[key] = eval(f"update.{key}")
        except AttributeError:
            key_values[key] = None

    return key_values


async def processor(update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:

    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        data_to_insert_to_db = []
        invalid_queries = []
    else:
        raise Exception('Chat ID is None')

    if update.effective_user:
        if update.effective_user.first_name:
            user_first_name = update.effective_user.first_name
        elif update.effective_user.username:
            user_first_name = update.effective_user.username
        else:
            user_first_name = 'Added from Telegram'
    else:
        user_first_name = 'Added from Telegram'

    conn = mylib.PostgresDatabase(dbname=DBNAME,
                                  user=USER,
                                  password=PASSWORD,
                                  host=HOST,
                                  port=PORT).get_connection
    if mylib.PostgresDatabase.validate_user(str(chat_id), conn):
        query_list = mylib.Spending.split_query_string(update.message.text)
    else:
        text = '''Понимаю любопытсво, но это личная информация.
Необходимо добавить ваш ID в список разрешенных.
Спасибо за понимание.'''
        await update.message.reply_text(text)
        return
    for query in query_list:
        try:
            valid_data = mylib.Spending.validate(query)
            required_keys = ['spending_name',
                             'spending_source',
                             'spending_cost']
            if not all(key in valid_data for key in required_keys):
                raise KeyError(
                    f"""Отсутствует один или несколько обязательных ключей:
                    {required_keys}"""
                    )

            # Создание объекта с проверенными значениями
            spending = mylib.Spending(
                spending_name=valid_data['spending_name'],
                spending_source=valid_data['spending_source'],
                spending_cost=valid_data['spending_cost']
            )
            data_to_insert_to_db.append(spending)
        except Exception as err:
            invalid_queries.append(query)
            logging.error(err)
            await update.message.reply_text(f'Ошибка! Расход не учтен. {err}')

    if data_to_insert_to_db:
        # mylib.PostgresDatabase().add_data(spendings=data_to_insert_to_db,
        #                                   buyer_name=user_first_name,
        #                                   conn=conn)
        spendings_summary = mylib.Spending.summarize_spendings(
            data_to_insert_to_db
        )
        text = f'''Данные успешно добавлены:
{spendings_summary}
'''
        await update.message.reply_text(text)

    if invalid_queries:
        text = f'Некорректные данные: {invalid_queries}'
        await update.message.reply_text(text)

    undef_categories = mylib.PostgresDatabase.get_undefined_categories_amount(
        conn)
    if undef_categories:
        text = f'Категории не определены: {undef_categories}'
        await update.message.reply_text(text)
    conn.close()


def main():
    start_dashboard()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('help', telegram_help_text))
    app.add_handler(CommandHandler('start', telegram_start_text))
    app.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND), processor))
    app.run_polling()


if __name__ == '__main__':
    main()
