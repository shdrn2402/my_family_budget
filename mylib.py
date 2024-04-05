import abc
import csv
import re
from datetime import datetime, time

import psycopg2

# TODO add documentation
# TODO add triggers to DB, creating new tables for new users
# TODO add unit tests for all functions and classes
# TODO add spendings analysis in bot and desktop app
# TODO add purchases categories besides names


class Note(abc.ABC):

    # def __init__(self, string: str):
    #     """
    #     Initializes an object of the Note class.
    #     """
    #     self.string = string
    #     self.date = datetime.now()

    # @classmethod
    # def create_with_date(cls, string: str, note_date: str) -> 'Note':
    #     """
    #     Alternative constructor. With options to specify date.
    #     Using in desktop_app.py"""
    #     _note = cls(string)
    #     _note.date = datetime.strptime(
    #         note_date, '%Y-%m-%d %H:%M:%S')
    #     return _note

    def __init__(self, string, **kwargs) -> None:
        """
        Initializes an object of the Note class.
        """
        self._query_string = re.sub(r'(\d+),(\d+)', r'\1.\2', string)
        if kwargs.get('date'):
            self._date = datetime.strptime(
                kwargs.get('date'), '%Y-%m-%d %H:%M:%S'
            )
        else:
            self._date = datetime.now()
        self._query_list = self.split_query_string()

    def split_query_string(self) -> list:
        """
        Splits query string into list of strings.
        """
        if ',' in self.query_string:
            query_list = self.query_string.split(',')
        else:
            query_list = [self.query_string]
        return list(map(str.strip, query_list))

    @abc.abstractmethod
    def validate(self) -> None:
        """
        Performs all validation checks.
        """
        pass

    @abc.abstractmethod
    def add_note(self) -> None:
        """
        Adds note to database.
        """
        pass

    @abc.abstractmethod
    def get_note_date(self) -> str:
        """
        Returns the date of the note.
        """
        pass

    @abc.abstractmethod
    def update_note(self) -> None:
        """
        Updates note in database.
        """
        pass


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
        self._spending_datetime = datetime.now()
        self._spending_name = spending[0]
        self._spending_source = spending[1]
        self._spending_cost = spending[2]

    @classmethod
    def create_with_date(cls, spending: list, sp_date: str) -> 'Spending':
        """
        Alternative constructor. With options to specify date.
        Using in desktop_app.py"""
        _spending = cls(spending)
        _spending._spending_date = datetime.strptime(
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
        return self._spending_name.capitalize()

    @property
    def spending_source(self) -> str:
        if self._spending_source in Spending.bank:
            return 'Bank'
        elif self._spending_source in Spending.card:
            return 'Card'
        else:
            return 'Cash'

    @property
    def spending_cost(self) -> float:
        return float(self._spending_cost)

    @property
    def spending_datetime(self) -> datetime:
        return self._spending_datetime

    def __str__(self) -> str:
        return f'''Цель: {self.spending_name}
Источник: {self.spending_source}
Сумма: {self.spending_cost}
Дата: {self.spending_datetime.strftime('%d-%m-%Y')}'''


class Database(abc.ABC):
    """Abstract class for working with expense data.

    Abstract methods:
        __init__(self, spending: Spending,
                 buyer_name
                 : str): Class constructor.
        prepare_data(self): Prepares data for insertion to database.
        add_data_to_csv(self, **kwargs): Adds data to database.
    """
    @abc.abstractmethod
    def __init__(self, spending: Spending, buyer_name: str):
        """
        Initializes an object of the DataBase class.

        Parameters:
        spending: An object of the Spending class
        buyer_name
        : str
            User's name.
        """
        self._spending = spending
        self._buyer_name = buyer_name

    @abc.abstractmethod
    def add_data(self, **kwargs):
        '''Absract method for adding data to database.'''
        pass

    @property
    def buyer_name(self) -> str:
        andrey = ['Andrew', 'Andrey', 'Андрей', '🇮🇱Andrey🇮🇱']
        ekaterina = ['Ekaterina', 'Екатерина']
        if self._buyer_name in andrey:
            return 'Andrey'
        elif self._buyer_name in ekaterina:
            return 'Ekaterina'
        else:
            return self._buyer_name


class CsvDatabase(Database):
    """Class for adding expense data to a CSV file.

    Methods:
    __init__(self,
            spending: Spending,
            buyer_name
            : str): Class constructor.
    prepare_data(self): Prepares data for CSV writing.
    add_datav(self, csv_file_path): Adds data to a CSV file.
    """

    def __init__(self, spending: Spending, buyer_name: str):
        """
        Initializes an object of the CsvDatabase class.

        Parameters:
        spending (Spending): An object of the Spending class.
        buyer_name
        : str
            User's name.
        """
        super().__init__(spending, buyer_name
                         )
        self._spending_datetime = self._spending.spending_datetime
        self._spending_year = self._spending_datetime.strftime('%Y')
        self._spending_month = self._spending_datetime.strftime('%m')
        self._spending_day = self._spending_datetime.strftime('%d')
        self._spending_weekday = self._spending_datetime.strftime('%a')
        self._spending_date = self._spending_datetime.date()
        spending_time = self._spending_datetime.time()
        self._spending_time = time(spending_time.hour,
                                   spending_time.minute)

    def prepare_data(self) -> list:
        return [
            self._spending.spending_name,
            self._spending.spending_source,
            self._spending.spending_cost,
            self._spending_time,
            self._spending_date,
            self._spending_year,
            self._spending_month,
            self._spending_day,
            self._spending_weekday,
            self.buyer_name
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


class PostgresDatabase(Database):

    def __init__(self, **kwargs):
        self._dbname = kwargs.get('dbname')
        self._user = kwargs.get('user')
        self._password = kwargs.get('password')
        self._host = kwargs.get('host')
        self._port = kwargs.get('port')

    @property
    def get_connection(self):
        return psycopg2.connect(
            dbname=self._dbname,
            user=self._user,
            password=self._password,
            host=self._host,
            port=self._port
        )

    def add_data(self,
                 spending: Spending,
                 buyer_name: str,
                 conn):
        cur = conn.cursor()
        query = '''
        INSERT INTO budget.budget (
            purchase_name,
            purchase_category,
            price,
            financing_source,
            purchase_date,
            buyers_name)
            VALUES (%s, %s, %s, %s, %s, %s);'''
        cur.execute(query, (spending.spending_name,
                            'Undefined',
                            spending.spending_cost,
                            spending.spending_source,
                            spending.spending_datetime,
                            buyer_name))
        conn.commit()
        cur.close()
