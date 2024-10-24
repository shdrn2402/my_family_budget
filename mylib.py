import abc
import logging
import re
from datetime import datetime, time
from typing import List, Optional

import psycopg
from telegram import Update
from telegram.ext import ContextTypes

# TODO add deletion and update functionality to Spending class
# TODO add documentation
# TODO add unit tests for all functions and classes
# TODO add spendings analysis in bot and desktop app

logging.basicConfig(filename='logs/app.log',
                    level=logging.INFO,
                    encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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

    def __init__(self, spending_name: str, spending_source: str,
                 spending_cost: float, **kwargs):
        """
        Initializes an object of the Spending class.

        :param spending_name: Name of the spending.
        :param spending_source: Source of the spending.
        :param spending_cost: Cost of the spending.
        """
        super().__init__(**kwargs)  # Initialize parent class (Note) with remaining kwargs
        self._spending_name = spending_name
        self._spending_source = spending_source
        self._spending_cost = spending_cost

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
    def validate(query: str) -> dict:
        """
        Validates the spending data (name, source, and cost).

        :param query: The query string to validate.
        :return: A dictionary with validated spending data.
        :raises ValueError: If any of the required fields are missing or invalid.
        """
        *name, source, cost = query.split()
        full_name = ' '.join(name)

        if not full_name:
            raise ValueError(f'''Наименование траты не может быть пустым!
                             {Spending.frmt_msg}''')
        
        try:
            float(cost)
        except ValueError:
            raise ValueError(f'''Сумма траты должна быть числом!
                             {Spending.frmt_msg}''')

        if not source:
            raise ValueError(f'''Источник траты не может быть пустым!
                             {Spending.frmt_msg}''')

        return {
            'spending_name': full_name,
            'spending_source': source,
            'spending_cost': float(cost)
        }

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


class User:
    """
    Class representing a user.

    Attributes:
        id: Unique user identifier (Telegram ID).
        family_id: Family identifier. For the main user, it matches id.
        first_name: User's first name.
        Defaults to 'undefined' for additional users.
        language: The language used by the user.
        Defaults to 'undefined' for additional users.
        created_at: The date the user object was created.
        verified: Whether the user is verified (fully registered).
        main_user: Indicates if the user is the main user (has full rights).
        read_only: Indicates if the user has read-only access.
    """

    def __init__(self, id: int, first_name: str, language: str,
                 family_id: Optional[int] = None, verified: bool = True,
                 main_user: bool = True, read_only: bool = False):
        """
        Initializes a main user (or additional user if specified).

        :param id: Unique user identifier (Telegram ID).
        :param first_name: The user's first name.
        :param language: The user's language.
        :param family_id: The family identifier of the user.
        :param verified: Whether the user is verified. Defaults to True.
        :param main_user: Whether the user is the main user. Defaults to True for main users.
        :param read_only: Whether the user has read-only access. Defaults to False for main users.
        """
        self._id = id
        self._first_name = first_name
        self._language = language
        self._created_at = datetime.now().replace(microsecond=0)
        self._family_id = family_id if family_id is not None else id  # For the main user, family_id is equal to id by default
        self._verified = verified
        self._main_user = main_user
        self._read_only = read_only

    @classmethod
    def create_additional_user(cls, id: int, family_id: int,
                               first_name: str = "undefined",
                               language: str = "undefined",
                               read_only: bool = True):
        """
        Alternative constructor for creating an additional user.

        :param id: Unique user identifier (Telegram ID).
        :param family_id: The family identifier of the main user.
        :param first_name: The user's first name. Defaults to 'undefined'.
        :param language: The user's language. Defaults to 'undefined'.
        :param read_only: Indicates if the user has read-only access. Defaults to True for additional users.
        :return: A new User object for an additional user.
        """
        verified = first_name != "undefined" and language != "undefined"  # Verified if full data is provided
        return cls(id=id, first_name=first_name, language=language,
                   family_id=family_id, main_user=False, read_only=read_only,
                   verified=verified)

    @property
    def id(self) -> int:
        """Returns the user's unique identifier."""
        return self._id

    @property
    def family_id(self) -> int:
        """Returns the user's family ID."""
        return self._family_id

    @property
    def first_name(self) -> str:
        """Returns the user's first name."""
        return self._first_name

    @property
    def language(self) -> str:
        """Returns the user's language."""
        return self._language

    @property
    def created_at(self) -> datetime:
        """Returns the timestamp when the user was created."""
        return self._created_at

    @property
    def verified(self) -> bool:
        """Returns whether the user is verified."""
        return self._verified

    @property
    def main_user(self) -> bool:
        """Returns whether the user is the main user."""
        return self._main_user

    @property
    def read_only(self) -> bool:
        """Returns whether the user has read-only access."""
        return self._read_only

    @classmethod
    def validate_main_user(cls, update: Update) -> dict:
        """
        Validates the main user's data and retrieves it as a dictionary.

        :param update: The update object containing the main user's data.
        :return: A dictionary containing the main user's data.
        """
        pass


    @classmethod
    def validate_additional_user(cls, update: Update,
                                 context: ContextTypes.DEFAULT_TYPE) -> dict:
        """
        Validates the additional user's data and retrieves it as a dictionary.

        :param update: The update object containing the additional user's data.
        :return: A dictionary containing the additional user's data.
        """
        pass

# if __name__ == '__main__':
#     spending_list = [Spending(spending_name="Кофе", spending_source="Кофейня", spending_cost=3.5),
#                      Spending(spending_name="Хлеб", spending_source="Магазин", spending_cost=2.0),
#                      Spending(spending_name="Молоко", spending_source="Магазин", spending_cost=1.5)]

#     total_cost = Spending.summarize_spendings(spending_list)
#     print(total_cost)