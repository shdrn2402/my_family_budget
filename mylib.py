import abc
import csv
import re
from datetime import datetime, time

import psycopg2
from typing import List

# TODO add documentation
# TODO add unit tests for all functions and classes
# TODO add spendings analysis in bot and desktop app


class Note(abc.ABC):
    def __init__(self, string: str):
        """
        Initializes an object of the Note class.
        
        :param string: The input string containing the note details.
        """
        self._string = string
        self._date = datetime.now()

    @classmethod
    def create_with_date(cls, string: str, note_date: str) -> 'Note':
        """
        Alternative constructor with options to specify a custom date.
        
        :param string: The input string containing the note details.
        :param note_date: A string representing the date in the format '%Y-%m-%d %H:%M:%S'.
        :return: An instance of the Note class with the specified date.
        """
        _note = cls(string)
        _note._date = datetime.strptime(note_date, '%Y-%m-%d %H:%M:%S')
        return _note

    @property
    def string(self) -> str:
        """
        Returns the string attribute.
        
        :return: The input string.
        """
        return self._string

    @property
    def date(self) -> datetime:
        """
        Returns the date attribute.
        
        :return: The datetime object representing when the note was created or assigned.
        """
        return self._date

    def split_query_string(self) -> List[str]:
        """
        Splits the input query string into a list of strings (handles multiple entries).
        
        :return: A list of individual query strings.
        """
        if ',' in self._string:
            query_list = self._string.split(',')
        else:
            query_list = [self._string]
        # Strips extra spaces and filters out empty entries
        return list(map(str.strip, query_list))

    @abc.abstractmethod
    def add_note(self) -> None:
        """
        Adds the note to the database.
        This method must be implemented in a subclass.
        """
        pass

    @abc.abstractmethod
    def del_note(self) -> None:
        """
        Deletes the note from the database.
        This method must be implemented in a subclass.
        """
        pass

    @abc.abstractmethod
    def update_note(self) -> None:
        """
        Updates the note in the database.
        This method must be implemented in a subclass.
        """
        pass

    @abc.abstractmethod
    def __str__(self) -> str:
        """
        Converts the note to a string representation.
        This method must be implemented in a subclass.
        
        :return: A string representation of the note.
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
        self._spending_datetime = datetime.now().replace(microsecond=0)
        self._spending_name = spending[0]
        self._spending_source = spending[1].lower()
        self._spending_cost = spending[2]

    @classmethod
    def create_with_date(cls, spending: list, sp_date: str) -> 'Spending':
        """
        Alternative constructor. With options to specify date.
        Using in desktop_app.py"""
        _spending = cls(spending)
        _spending._spending_datetime = datetime.strptime(
            sp_date, '%Y-%m-%d %H:%M:%S')
        return _spending

    @staticmethod
    def validate_format(spending_list: list) -> None:
        if len(spending_list) != 3:
            raise ValueError(f'Неверный формат данных!{Spending.frmt_msg}')

    @staticmethod
    def validate_spending_name(spending_list: list) -> None:
        try:
            float(spending_list[0])
        except ValueError:
            pass
        else:
            raise ValueError(
                f'Первый параметр не может быть числом!{Spending.frmt_msg}'
            )

    @staticmethod
    def validate_cost(spending_list: list) -> None:
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
        Spending.validate_cost(spending_list)

    @property
    def spending_name(self) -> str:
        return self._spending_name.capitalize()

    @property
    def spending_source(self) -> str:
        return self._spending_source

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
    def prepare_data(self):
        '''Absract method for preparing data for insertion to database.'''
        pass

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
        self._connection = None
        self._purchase_category = 'Undefined'
        self._purchase_subcategory = 'Undefined'
        self._purchase_source = 'Undefined'

    @property
    def get_connection(self):
        if self._connection is None:
            self._connection = psycopg2.connect(
                dbname=self._dbname,
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port
            )
        return self._connection

    @staticmethod
    def validate_user(tg_id: str, conn) -> bool:
        cur = conn.cursor()
        query = '''
        SELECT EXISTS (
            SELECT 1
            FROM budget.users
            WHERE tg_id = %s
        );
        '''
        cur.execute(query, (tg_id,))
        user_exists = cur.fetchone()
        cur.close()
        return user_exists[0]

    @staticmethod
    def get_undefined_categories_amount(conn) -> int:
        cur = conn.cursor()
        query = '''
        SELECT COUNT(*)
        FROM budget.budget
        WHERE purchase_subcategory = 'Undefined';
        '''
        cur.execute(query)
        count_undefined_categories = cur.fetchone()
        cur.close()
        return count_undefined_categories[0]

    def prepare_data(self,
                     purchase_name: str,
                     source_name: str,
                     conn):
        cur = conn.cursor()
        query = '''
        SELECT purchase_subcategory
        FROM budget.budget
        WHERE purchase_name = %s;
        '''
        cur.execute(query, (purchase_name,))
        existing_category = cur.fetchone()
        if existing_category:
            self._purchase_subcategory = existing_category[0]

        query = '''
        SELECT  category_name
        FROM budget.purchase_category_subcategory
        WHERE subcategory_name = %s;
        '''
        cur.execute(query, (self._purchase_subcategory,))
        category_name = cur.fetchone()
        if category_name:
            self._purchase_category = category_name[0]

        query = '''
        SELECT source_name_db
        FROM budget.sources
        WHERE source_name = %s;
        '''
        cur.execute(query, (source_name,))
        source_name_db = cur.fetchone()
        if not source_name_db:
            raise ValueError(f'Недействительный источник трат: {source_name}')
        else:
            self._purchase_source = source_name_db[0].capitalize()

        cur.close()

    def add_data(self,
                 spending: Spending,
                 buyer_name: str,
                 conn):

        self.prepare_data(spending.spending_name,
                          spending.spending_source,
                          conn)
        cur = conn.cursor()
        query = '''
        INSERT INTO budget.budget (
            purchase_name,
            purchase_subcategory,
            price,
            financing_source,
            purchase_date,
            buyers_name,
            purchase_category)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            '''
        formatted_datetime = spending.spending_datetime.strftime(
            '%Y-%m-%d %H:%M:%S')
        cur.execute(query, (spending.spending_name,
                            self._purchase_subcategory,
                            spending.spending_cost,
                            self._purchase_source,
                            formatted_datetime,
                            buyer_name,
                            self._purchase_category))
        conn.commit()
        cur.close()
