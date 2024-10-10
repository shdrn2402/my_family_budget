import abc
import csv
from datetime import datetime, time

import psycopg2
import re
from typing import List

# TODO add deletion and update functionality to Spending class
# TODO add documentation
# TODO add unit tests for all functions and classes
# TODO add spendings analysis in bot and desktop app


class Note(abc.ABC):
    def __init__(self, **kwargs):
        """
        Initializes an object of the Note class.

        :param string: The input string containing the note details.
        """
        self._date = datetime.now().replace(microsecond=0)

    @classmethod
    def create_with_date(cls, note_date: str, **kwargs) -> 'Note':
        """
        Alternative constructor with options to specify a custom date.

        :param string: The input string containing the note details.
        :param note_date: A string representing the date in the format
        '%Y-%m-%d %H:%M:%S'.
        :return: An instance of the Note class with the specified date.
        """
        _note = cls(**kwargs)
        _note._date = datetime.strptime(note_date, '%Y-%m-%d %H:%M:%S')
        return _note

    @property
    def date(self) -> datetime:
        """
        Returns the date attribute.

        :return: The datetime object representing when the note was created
        or assigned.
        """
        return self._date

    @staticmethod
    @abc.abstractmethod
    def split_query_string(query_str: str) -> List[str]:
                """
        Splits the input query string into a list of strings
        (handles multiple entries).

        :param query_str: The input query string.
        :return: A list of individual query strings.
        """
        pass

    @abc.abstractmethod
    def validate(self, spending: str) -> dict:
        """
        Validates the note data.

        :param spending: The input spending data as a string.
        :return: A dictionary containing validated spending data.
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


class Spending(Note):
    """Class to represent information about expenses."""

    frmt_msg = '''
Для добавления расходов необходимо использовать следующий формат:
[наименование траты - str] [источник траты - str] [сумма траты - float]
'''

    def __init__(self, **kwargs):
        """
        Initializes an object of the Spending class.

        :param kwargs: Keyword arguments containing spending details.
        """
        super().__init__(**kwargs)
        self._spending_name = kwargs.get('spending_name', None)
        self._spending_source = kwargs.get('spending_source', None)
        self._spending_cost = kwargs.get('spending_cost', None)

    @staticmethod
    def split_query_string(query_str: str) -> List[str]:
        """
        Splits the input query string into a list of strings
        (handles multiple entries).

        :param query_str: The input query string to split.
        :return: A list of individual query strings.
        """
        query_str = re.sub(r'(\d+),(\d+)', r'\1.\2', query_str)
        if ',' in query_str:
            query_list = query_str.split(',')
        else:
            query_list = [query_str]
        return list(map(str.strip, query_list))

    @staticmethod
    def validate_spending_name(name: str) -> None:
        """
        Validates the spending name to ensure it is not a number.

        :param name: The name of the spending to validate.
        """
        try:
            float(name)
        except ValueError:
            pass
        else:
            raise ValueError(
                f'Первый параметр не может быть числом!{Spending.frmt_msg}'
            )

    @staticmethod
    def validate_cost(spending: str) -> None:
        """
        Validates the cost to ensure it is a valid number.

        :param spending: The cost to validate.
        """
        try:
            float(spending)
        except ValueError:
            raise ValueError(
                f'Третий параметр должен быть числом!{Spending.frmt_msg}'
            )

    @staticmethod
    def validate(query: str) -> dict:
        """
        Validates the spending data (name, source, and cost).

        :param query: The query string to validate.
        :return: A dictionary with validated spending data.
        """
        *name, source, cost = query.split()
        full_name = ' '.join(name)
        if all([full_name, source, cost]):
            Spending.validate_spending_name(full_name)
            Spending.validate_cost(cost)
        else:
            raise ValueError(f'Не хватает данных!{Spending.frmt_msg}')
        return {'spending_name': full_name,
                'spending_source': source,
                'spending_cost': cost}

    @staticmethod
    def summarize_spendings(spendings: List['Spending']) -> str:
        """
        Returns a summary of the spendings.

        :param spendings: A list of spending objects to summarize.
        :return: A summary string of the total number and cost of spendings.
        """
# TODO add grouping by date
        total_spendings_amount = 0
        total_cost = 0.0
        for spending in spendings:
            total_spendings_amount += 1
            total_cost += spending.spending_cost
        return f'''Количество покупок: {total_spendings_amount}
Общая стоимость покупок: {total_cost}
'''

    @property
    def spending_name(self) -> str:
        return self._spending_name.lower()

    @property
    def spending_source(self) -> str:
        return self._spending_source.lower()

    @property
    def spending_cost(self) -> float:
        return float(self._spending_cost)

    @property
    def spending_date(self) -> datetime:
        return self._date

    def __str__(self) -> str:
        """
        Returns a string representation of the spending.
        """
        return f'''Цель: {self.spending_name}
Источник: {self.spending_source}
Сумма: {self.spending_cost}
Дата: {self.spending_date.strftime('%d-%m-%Y')}'''


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
                 spendings: list['Spending'],
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


# if __name__ == '__main__':
#     spending_list = [Spending(spending_name="Кофе", spending_source="Кофейня", spending_cost=3.5),
#                      Spending(spending_name="Хлеб", spending_source="Магазин", spending_cost=2.0),
#                      Spending(spending_name="Молоко", spending_source="Магазин", spending_cost=1.5)]

#     total_cost = Spending.summarize_spendings(spending_list)
#     print(total_cost)