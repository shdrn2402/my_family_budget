import abc
import csv
from datetime import datetime, time


class Spending:
    """Class to represent information about expenses.

    Attributes:
        bank: list
            List of keywords for bank expenses
        card: list
            List of keywords for card expenses
        cash: list
            List of keywords for cash expenses
        frmt_msg: str
            Message with correct input example

    Methods:
        __init__(self, spending: str): Class constructor.
        validate_format(self, spending_list): Checks input format.
        validate_spending_name(self, spending_list): Checks expense name.
        validate_source(self, spending_list): Checks expense source.
        validate_cost(self, spending_list): Checks expense cost.
        validate(self, spending_list): Performs all validation checks.
        spending_name(self): Returns formatted expense name.
        spending_source(self): Returns expense source.
        spending_cost(self): Returns expense cost.
        spending_date(self): Returns the date of the expense.
        get_spending_time(self): Returns the time of the expense.
        get_spending_ymdw(self, flag: str): Returns date and time components.
        __str__(self): Returns a string representation of the expense.
    """

    bank = ['чек', 'чеки', 'банк', 'check', 'bank']
    card = ['карта', 'кредитка', 'ашрай', 'card', 'credit']
    cash = ['нал', 'наличные', 'кэш', 'кеш', 'cash', 'money']
    frmt_msg = '''
Для добавления расходов необходимо использовать следующий формат
[наименование траты - str] [источник траты - str] [сумма траты - str]
'''

    def __init__(self, spending: list):
        """
        Initializes an object of the Spending class.

        Parameters:
        spending: list
            List of data to be added in the format [name, source, amount].
        """
        self.__spending_date = datetime.now()
        self.__spending_name = spending[0]
        self.__spending_source = spending[1]
        self.__spending_cost = spending[2]

    @classmethod
    def create_with_date(cls, spending: list, sp_date: str) -> 'Spending':
        """
        Alternative constructor. With options to specify date.
        Using in desktop_app.py"""
        _spending = cls(spending)
        _spending.__spending_date = datetime.strptime(
            sp_date, '%Y-%m-%d %H:%M:%S')
        return _spending

    @staticmethod
    def validate_format(spending_list) -> None:
        if len(spending_list) != 3:
            raise ValueError(f'Неверный формат данных!{Spending.frmt_msg}')

    @staticmethod
    def validate_spending_name(spending_list) -> None:
        try:
            float(spending_list[0])
        except ValueError:
            pass
        else:
            raise ValueError(
                f'Первый параметр не может быть числом!{Spending.frmt_msg}'
            )

    @staticmethod
    def validate_source(spending_list) -> None:
        source = spending_list[1].lower()
        all_sources = Spending.bank + Spending.card + Spending.cash

        if source not in all_sources:
            raise ValueError(f'Недействительный источник трат: {source}')

    @staticmethod
    def validate_cost(spending_list) -> None:
        try:
            float(spending_list[2])
        except ValueError:
            raise ValueError(
                f'Третий параметр должен быть числом!{Spending.frmt_msg}'
            )

    @staticmethod
    def validate(spending_list) -> None:
        Spending.validate_format(spending_list)
        Spending.validate_spending_name(spending_list)
        Spending.validate_source(spending_list)
        Spending.validate_cost(spending_list)

    @property
    def spending_name(self) -> str:
        return self.__spending_name.capitalize()

    @property
    def spending_source(self) -> str:
        if self.__spending_source in Spending.bank:
            return 'Bank'
        elif self.__spending_source in Spending.card:
            return 'Card'
        else:
            return 'Cash'

    @property
    def spending_cost(self) -> float:
        return float(self.__spending_cost)

    @property
    def spending_date(self) -> datetime:
        return self.__spending_date.date()

    def get_spending_time(self) -> time:
        spending_time = self.__spending_date.time()
        spending_time = time(spending_time.hour,
                             spending_time.minute)
        return spending_time

    def get_spending_ymdw(self, flag: str) -> str:
        if flag == 'year':
            return self.__spending_date.strftime('%Y')
        elif flag == 'month':
            return self.__spending_date.strftime('%m')
        elif flag == 'day':
            return self.__spending_date.strftime('%d')
        elif flag == 'weekday':
            return self.__spending_date.strftime('%a')
        else:
            raise ValueError(f'Неверная дата!{Spending.frmt_msg}')

    def __str__(self) -> str:
        return f'''Цель: {self.spending_name}
Источник: {self.spending_source}
Сумма: {self.spending_cost}
Дата: {self.spending_date.strftime('%d-%m-%Y')}'''


class Database(abc.ABC):
    """Abstract class for working with expense data.

    Abstract methods:
        __init__(self, spending: Spending,
                 spender_name: str): Class constructor.
        prepare_data(self): Prepares data for insertion to database.
        add_data_to_csv(self, **kwargs): Adds data to database.
    """
    @abc.abstractmethod
    def __init__(self, spending: Spending, spender_name: str):
        """
        Initializes an object of the DataBase class.

        Parameters:
        spending: An object of the Spending class
        spender_name: str
            User's name.
        """
        self._spending = spending
        self._spender_name = spender_name

    @abc.abstractmethod
    def prepare_data(self):
        '''Absract method for preparing data for insertion to database.
        '''
        pass

    @abc.abstractmethod
    def add_data(self, **kwargs):
        '''Absract method for adding data to database.'''
        pass


class CsvDatabase(Database):
    """Class for adding expense data to a CSV file.

    Methods:
    __init__(self,
            spending: Spending,
            spender_name: str): Class constructor.
    prepare_data(self): Prepares data for CSV writing.
    add_datav(self, csv_file_path): Adds data to a CSV file.
    """

    def __init__(self, spending: Spending, spender_name: str):
        """
        Initializes an object of the CsvDatabase class.

        Parameters:
        spending (Spending): An object of the Spending class.
        spender_name: str
            User's name.
        """
        super().__init__(spending, spender_name)

    def prepare_data(self) -> list:
        spending_year = self._spending.get_spending_ymdw('year')
        spending_month = self._spending.get_spending_ymdw('month')
        spending_day = self._spending.get_spending_ymdw('day')
        spending_weekday = self._spending.get_spending_ymdw('weekday')
        return [
            self._spending.spending_name,
            self._spending.spending_source,
            self._spending.spending_cost,
            self._spending.get_spending_time(),
            self._spending.spending_date,
            spending_year,
            spending_month,
            spending_day,
            spending_weekday,
            self._spender_name
        ]

    def add_data(self, csv_file_path: str) -> None:
        data = self.prepare_data()
        try:
            with open(
                csv_file_path,
                mode='a',
                newline='',
                encoding='utf-8-sig'
            ) as file:
                writer = csv.writer(file)
                writer.writerow(data)
        except FileNotFoundError:
            raise FileNotFoundError(f'Нет такого файла: {csv_file_path}')
        except PermissionError:
            raise PermissionError(f'Нет доступа к файлу: {csv_file_path}')
        except Exception as error:
            raise error


if __name__ == '__main__':

    s1 = Spending(['Карта', 'Овощи', '1000'])
    print(s1.__dict__)
    print()
    s2 = Spending.create_with_date(
        ['Карта', 'Овощи', '10000'], sp_date='2023-10-01 15:11:22')
    print(s2.__dict__)
    # CsvDatabase(s2, 'Andrew').add_data('data/budget.csv')
