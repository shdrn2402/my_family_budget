import logging
import os.path
import re

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
WHITELIST = os.environ.get('WHITE_LIST').split(' ')


def get_query_list(query_str: str) -> list:
    if ',' in query_str:
        query_list = query_str.split(',')
    else:
        query_list = [query_str]
    return list(map(str.strip, query_list))


async def telegram_help_text(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> None:
    """This function is used to send help message.
    """
    user_first_name = update.effective_user.first_name
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
    """This function is used to send welcome messages.
    """
    user_first_name = update.effective_user.first_name
    text = f'''Привет, {user_first_name},
Это бот для ведения сейного бюджета в google sheets с помощью telegram.
В данный момент это закрытый бот.
Функциональность ограничена для тестирования.
Используй /help для получения списка команд.'''
    await update.message.reply_text(text)


def is_user_in_white_list(user_id: str) -> bool:
    return user_id in WHITELIST


async def processor(update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_first_name = update.effective_user.first_name

    if is_user_in_white_list(str(chat_id)):
        query_str = re.sub(r'(\d+),(\d+)', r'\1.\2', update.message.text)
        query_list = get_query_list(query_str)
    else:
        text = '''Понимаю любопытсво, но это личная информация.
Необходимо добавить ваш ID в список разрешенных.
Спасибо за понимание.'''
        await update.message.reply_text(text)
        return

    for query_str in query_list:
        try:
            *name, source, amount = query_str.split()
            q_list = [' '.join(name), source, amount]
            mylib.Spending.validate(q_list)
            spending = mylib.Spending(q_list)
            mylib.CsvDatabase(spending, user_first_name).add_data(data_path)
            text = f'''Данные успешно добавлены:
{str(spending)}
'''
            await update.message.reply_text(text)
        except Exception as err:
            logging.error(err)
            await update.message.reply_text(f'Ошибка! Расход не учтен. {err}')


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('help', telegram_help_text))
    app.add_handler(CommandHandler('start', telegram_start_text))
    app.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND), processor))
    app.run_polling()


if __name__ == '__main__':
    main()
