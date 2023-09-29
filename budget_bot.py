import logging
import os.path
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from mylib import DataBase, Spending

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


def get_query_list(query_str):
    if ',' in query_str:
        query_list = query_str.split(',')
    else:
        query_list = [query_str]
    return list(map(str.strip, query_list))


async def telegram_help_text(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> None:
    '''This function is used to send help message.
    '''
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
При этом в каждом блоке может быть только одно наименование!
[наименование1] [источник1] [сумма1], [наименованиеN] [источникN] [суммаN]
'''
    await update.message.reply_text(text)


async def telegram_start_text(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    '''This function is used to send welcome messages.
    '''
    user_first_name = update.effective_user.first_name
    text = f'''Привет, {user_first_name},
Это бот для ведения сейного бюджета в google sheets с помощью telegram.
В данный момент это закрытый бот.
Функциональность ограничена для тестирования.
Используй /help для получения списка команд.'''
    await update.message.reply_text(text)


def is_user_in_white_list(user_id):
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
Ответственный за ведение бюджета должен добавить ваш ID в список разрешенных.
Спасибо за понимание.'''
        await update.message.reply_text(text)
        return
    for query_str in query_list:
        try:
            q_list = query_str.split(' ')
            Spending.validate(q_list)
            spending = Spending(q_list)
            DataBase(spending, user_first_name).add_data_to_csv(data_path)
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
