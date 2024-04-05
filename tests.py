
import csv
import os

import psycopg2
# import time
# # from datetime import datetime, time


# class Note():

#     def __init__(self, string, **kwargs):
#         """
#         Initializes an object of the Note class.
#         """
#         self.string = string
#         if kwargs.get('date'):
#             self.date = int(
#                 time.mktime(
#                     time.strptime(kwargs.get('date'), '%Y-%m-%d %H:%M:%S')
#                 )
#             )
#         else:
#             self.date = int(time.time())

#     def get_query_list(self) -> list:
#         if ',' in self.string:
#             query_list = self.string.split(',')
#         else:
#             query_list = [self.string]
#         return list(map(str.strip, query_list))


# test = Note(
#     'тест нал 25, тест2 банк 45'
# )

# print(test.string)
# print(test.date)


# test2 = Note(
#     'тест нал 25, тест2 банк 45',
#     date='2022-01-01 00:00:00'
# )

# print(test2.string)
# print(test2.date)

# print(test2.get_query_list())

# import psycopg2

# conn = psycopg2.connect("dbname=demo user=postgres password=Mr9Qt7St_P")
# cur = conn.cursor()
# cur.execute("SELECT * FROM bookings LIMIT 10;")
# print(cur.fetchall())
# conn.close()

# import psycopg2

# conn = psycopg2.connect("dbname=institute user=postgres password=Mr9Qt7St_P")
# cur = conn.cursor()

# user = 'shdrn'
# query = f"CREATE TABLE {user} (id integer, name char(15));"
# cur.execute(query)
# conn.commit()

# # Выполняем запрос на проверку наличия таблицы
# cur.execute(
#     "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'shdrn');")
# table_exists = cur.fetchone()[0]

# if table_exists:
#     print("Таблица 'shdrn' была успешно создана.")
# else:
#     print("Таблица 'shdrn' не была создана или что-то пошло не так.")

# conn.close()


# import time

# bank = ['чек', 'чеки', 'банк', 'check', 'bank']
# card = ['карта', 'кредитка', 'ашрай', 'card', 'credit']
# cash = ['нал', 'наличные', 'кэш', 'кеш', 'cash', 'money']


# def source(source: str) -> str:
#     if source in bank:
#         return ('Bank')
#     elif source in card:
#         return ('Card')
#     else:
#         return ('Cash')


# start = time.time()

# for i in range(10000000):
#     source('карта')

# print(f'Время выполнения со списками: {time.time() - start}')


# sources = {
#     'bank': ['чек', 'чеки', 'банк', 'check', 'bank'],
#     'card': ['карта', 'кредитка', 'ашрай', 'card', 'credit'],
#     'cash': ['нал', 'наличные', 'кэш', 'кеш', 'cash', 'money']
# }


# def source(source: str) -> str:
#     if source in sources['bank']:
#         return ('Bank')
#     elif source in sources['card']:
#         return ('Card')
#     else:
#         return ('Cash')


# start = time.time()
# for i in range(10000000):
#     source('карта')
# print(f'Время выполнения с словарем: {time.time() - start}')

# arguments = {
#     'a': 1,
#     'b': 2,
#     'c': 3
# }


# def print_arguments(**kwargs):
#     kwargs['d'] = 4
#     for key, value in kwargs.items():
#         print(key, value)


# print_arguments(**arguments)
# data_folder = 'data/'
# data_path = os.path.join(data_folder, 'budget.csv')

# conn = psycopg2.connect(
#     dbname='budget',
#     user='postgres',
#     password='Mr9Qt7St_P',
#     host='localhost',
#     port=5432
# )
# with open(data_path, newline='', encoding='utf-8-sig') as csvfile:
#     reader = csv.reader(csvfile, delimiter=',')
#     next(reader)

#     for row in reader:
#         purchase_name = row[0]
#         purchase_category = row[10]
#         price = row[2]
#         financing_source = row[1]
#         purchase_date = row[4] + ' ' + row[3]
#         buyers_name = row[9]

#         cur = conn.cursor()
#         query = '''
#         INSERT INTO budget.budget (
#             purchase_name,
#             purchase_category,
#             price,
#             financing_source,
#             purchase_date,
#             buyers_name)
#             VALUES (%s, %s, %s, %s, %s, %s);'''

#         cur.execute(query, (purchase_name,
#                             purchase_category,
#                             price,
#                             financing_source,
#                             purchase_date,
#                             buyers_name))
#         conn.commit()
#         cur.close()
