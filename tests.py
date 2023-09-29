# from datetime import datetime


# class Spending:
#     bank = ['чек', 'чеки', 'банк', 'check', 'bank']
#     card = ['карта', 'кредитка', 'ашрай', 'card', 'credit']
#     cash = ['нал', 'наличные', 'кэш', 'кеш', 'cash', 'money']

#     frmt_msg = '''
# Для добавления расходов необходимо использовать следующий формат
# [наименование траты - строка] [источник траты - строка] [сумма траты - число]
# '''

#     def __init__(self, spending: str):
#         self._spending_list = spending
#         self._spending_date = datetime.now()
#         self.__spending_name = self._spending_list[0].capitalize()

#     @staticmethod
#     def validate_format(spending_list) -> None:
#         if len(spending_list) != 3:
#             raise ValueError(f'Неверный формат данных!{Spending.frmt_msg}')

#     @staticmethod
#     def validate_spending_name(spending_list) -> None:
#         try:
#             float(spending_list[0])
#         except ValueError:
#             pass
#         else:
#             raise ValueError(
#                 f'Первый параметр не может быть числом!{Spending.frmt_msg}')

#     @staticmethod
#     def validate_source(spending_list) -> None:
#         source = spending_list[1]
#         all_sources = Spending.bank + Spending.card + Spending.cash
#         if source not in all_sources:
#             raise ValueError(f'Недействительный источник трат: {source}')

#     @staticmethod
#     def validate_cost(spending_list) -> None:
#         try:
#             float(spending_list[2])
#         except ValueError:
#             raise ValueError(
#                 f'Третий параметр должен быть числом!{Spending.frmt_msg}')

#     @staticmethod
#     def validate(spending_list) -> None:
#         Spending.validate_format(spending_list)
#         Spending.validate_spending_name(spending_list)
#         Spending.validate_source(spending_list)
#         Spending.validate_cost(spending_list)

#     @property
#     def spending_name(self) -> str:
#         return self.__spending_name


# print(Spending(['test', 'card',  '25']).spending_name)


try:
    print(float('25.ss8'))
except ValueError:
    raise ValueError
