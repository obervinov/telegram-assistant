"""This module contains a class for interacting with a PostgreSQL database using psycopg2"""
import os
import sys
import importlib
import json
import time
from typing import Union
import psycopg2
from psycopg2 import pool
from logger import log
from .tools import get_hash


def reconnect_on_exception(method):
    """
    A decorator that catches the closed cursor exception and reconnects to the database.
    """
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except psycopg2.Error as exception:
            log.warning('[Database]: Connection to the database was lost: %s. Attempting to reconnect...', str(exception))
            time.sleep(5)
            try:
                self.database_connections = self.create_connection_pool()
                log.info('[Database]: Reconnection successful.')
                return method(self, *args, **kwargs)
            except psycopg2.Error as inner_exception:
                log.error('[Database]: Failed to reconnect to the database: %s', str(inner_exception))
                raise inner_exception
    return wrapper


class DatabaseClient:
    """
    A class that represents a client for interacting with a PostgreSQL database.

    Attributes:
        database_connections (psycopg2.extensions.connection): A connection to the PostgreSQL database.
        vault (object): An object representing a HashiCorp Vault client for retrieving secrets.
        db_role (str): The role to use for generating database credentials.
        errors (psycopg2.errors): A collection of error classes for exceptions raised by the psycopg2 module.
        json (json): A JSON encoder and decoder for working with JSON data to execute database migrations.

    Methods:
        create_connection_pool(): Create a connection pool for the PostgreSQL database.
        get_connection(): Get a connection from the connection pool.
        close_connection(connection): Close the connection and return it to the connection pool.
        _prepare_db(): Prepare the database by creating and initializing the necessary tables.
        _migrations(): Execute database migrations to update the database schema or data.
        _is_migration_executed(migration_name): Check if a migration has already been executed.
        _mark_migration_as_executed(migration_name, version): Inserts a migration into the migrations table to mark it as executed.
        _create_table(table_name, columns): Create a new table in the database with the given name and columns if it does not already exist.
        _insert(table_name, columns, values): Inserts a new row into the specified table with the given columns and values.
        _select(table_name, columns, **kwargs): Selects rows from the specified table with the given columns based on the specified condition.
        _update(table_name, values, condition): Update the specified table with the given values of values based on the specified condition.
        _delete(table_name, condition): Delete rows from a table based on a condition.
        keep_message(message_id, chat_id, message_content, **kwargs): Add a message to the messages table in the database.
        get_users(only_allowed): Get a list of users from the users table in the database.
        get_considered_message(message_type, chat_id): Get a message with specified type and

    Rises:
        psycopg2.Error: An error occurred while interacting with the PostgreSQL database.
    """
    def __init__(self, vault: object = None, db_role: str = None) -> None:
        """
        Initializes a new instance of the Database client.

        Args:
            vault (object): An object representing a HashiCorp Vault client for retrieving secrets with the database configuration.
            db_role (str): The role to use for generating database credentials.

        Examples:
            To create a new instance of the Database class:
            >>> from modules.database import Database
            >>> from modules.vault import Vault
            >>> vault = Vault()
            >>> db = Database(vault=vault)
        """
        self.json = json
        self.vault = vault
        self.db_role = db_role
        self.errors = psycopg2.errors
        self.database_connections = self.create_connection_pool()

        self._prepare_db()
        self._migrations()

    def create_connection_pool(self) -> pool.SimpleConnectionPool:
        """
        Create a connection pool for the PostgreSQL database.

        Returns:
            pool.SimpleConnectionPool: A connection pool for the PostgreSQL database.
        """
        required_keys_configuration = {"host", "port", "dbname", "connections"}
        required_keys_credentials = {"username", "password"}
        db_configuration = self.vault.kv2engine.read_secret(path='configuration/database')
        db_credentials = self.vault.dbengine.generate_credentials(role=self.db_role)

        if not db_configuration or not db_credentials:
            raise ValueError('Database configuration or credentials are missing')

        missing_keys = (required_keys_configuration - set(db_configuration.keys())) | (required_keys_credentials - set(db_credentials.keys()))
        if missing_keys:
            raise KeyError("Missing keys in the database configuration or credentials: {missing_keys}")

        log.info(
            '[Database]: Creating a connection pool for the %s:%s/%s',
            db_configuration['host'], db_configuration['port'], db_configuration['dbname']
        )
        return pool.SimpleConnectionPool(
            minconn=1,
            maxconn=db_configuration['connections'],
            host=db_configuration['host'],
            port=db_configuration['port'],
            user=db_credentials['username'],
            password=db_credentials['password'],
            database=db_configuration['dbname']
        )

    def get_connection(self) -> psycopg2.extensions.connection:
        """
        Get a connection from the connection pool.

        Returns:
            psycopg2.extensions.connection: A connection to the PostgreSQL database.
        """
        return self.database_connections.getconn()

    def close_connection(self, connection: psycopg2.extensions.connection) -> None:
        """
        Close the cursor and return it to the connection pool.

        Args:
            connection (psycopg2.extensions.connection): A connection to the PostgreSQL database.
        """
        self.database_connections.putconn(connection)

    def _prepare_db(self) -> None:
        """
        Prepare the database by creating and initializing the necessary tables.
        """
        # Read configuration file for database initialization
        configuration_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../configs/databases.json'))
        with open(configuration_path, encoding='UTF-8') as config_file:
            database_init_configuration = json.load(config_file)

        # Create databases if does not exist
        for table in database_init_configuration.get('Tables', None):
            self._create_table(
                table_name=table['name'],
                columns="".join(f"{column}" for column in table['columns'])
            )
            log.info('[Database]: Prepare Database: create table `%s` (if does not exist)', table['name'])

        # Write necessary data to the database (service records)
        if database_init_configuration.get('DataSeeding', None):
            # ! This code block needs to be improved after some service data will appear for filling,
            # ! because this code creates duplicate lines each time the project is started.
            for data in database_init_configuration['DataSeeding']:
                self._insert(
                    table_name=data['table'],
                    columns=tuple(data['data'].keys()),
                    values=tuple(data['data'].values())
                )
                log.info('[Database]: Prepare Database: data seeding has been added to the `%s` table', data['table'])

    def _migrations(self) -> None:
        """
        Execute database migrations to update the database schema or data.
        """
        log.info('[Database]: Migrations: Preparing to execute database migrations...')
        # Migrations directory
        migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../migrations'))
        sys.path.append(migrations_dir)
        try:
            migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
            migration_files.sort()

            for migration_file in migration_files:
                if migration_file.endswith('.py'):
                    migration_module_name = migration_file[:-3]

                    if not self._is_migration_executed(migration_name=migration_module_name):
                        log.info('[Database]: Migrations: executing the %s migration...', migration_module_name)
                        migration_module = importlib.import_module(name=migration_module_name)
                        migration_module.execute(self)
                        version = getattr(migration_module, 'VERSION', migration_module_name)
                        self._mark_migration_as_executed(migration_name=migration_module_name, version=version)
                    else:
                        log.info('[Database] Migrations: the %s has already been executed and was skipped', migration_module_name)
                else:
                    log.error('[Database]: Migrations: the %s is not a valid migration file', migration_file)
        except FileNotFoundError as does_not_exist:
            log.info('[Database]: Migrations: no migration files found in the directory: %s', does_not_exist)

    def _is_migration_executed(self, migration_name: str = None) -> bool:
        """
        Check if a migration has already been executed.

        Args:
            migration_name (str): The name of the migration to check.

        Returns:
            bool: True if the migration has been executed, False otherwise.
        """
        return self._select(table_name='migrations', columns=('id',), condition=f"name = '{migration_name}'")

    def _mark_migration_as_executed(self, migration_name: str = None, version: str = None) -> None:
        """
        Inserts a migration into the migrations table to mark it as executed.

        Args:
            migration_name (str): The name of the migration to mark as executed.
        """
        self._insert(table_name='migrations', columns=('name', 'version'), values=(migration_name, version))

    def _create_table(self, table_name: str = None, columns: str = None) -> None:
        """
        Create a new table in the database with the given name and columns if it does not already exist.

        Args:
            table_name (str): The name of the table to create.
            columns (str): A string containing the column definitions for the table.

        Examples:
            To create a new table called 'users' with columns 'id' and 'name', you can call the method like this:
            >>> _create_table('users', 'id INTEGER PRIMARY KEY, name TEXT')
        """
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")
        conn.commit()
        self.close_connection(conn)

    @reconnect_on_exception
    def _insert(self, table_name: str = None, columns: tuple = None, values: tuple = None) -> None:
        """
        Inserts a new row into the specified table with the given columns and values.

        Args:
            table_name (str): The name of the table to insert the row into.
            columns (tuple): A tuple containing the names of the columns to insert the values into.
            values (tuple): A tuple containing the values to insert into the table.

        Examples:
            >>> db_client._insert(
            ...   table_name='users',
            ...   columns=('username', 'email'),
            ...   values=('john_doe', 'john_doe@example.com')
            ... )
        """
        try:
            sql_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql_query, values)
            conn.commit()
            self.close_connection(conn)
        except (psycopg2.Error, IndexError) as error:
            log.error(
                '[Database]: An error occurred while inserting a row into the table %s: %s\nColumns: %s\nValues: %s\nQuery: %s',
                table_name, error, columns, values, sql_query
            )

    @reconnect_on_exception
    def _select(self, table_name: str = None, columns: tuple = None, **kwargs) -> Union[list, None]:
        """
        Selects rows from the specified table with the given columns based on the specified condition.

        Args:
            table_name (str): The name of the table to select data from.
            columns (tuple): A tuple containing the names of the columns to select.

        Keyword Args:
            condition (str): The condition to use to select the data.
            order_by (str): The column to use for ordering the data.
            limit (int): The maximum number of rows to return.

        Returns:
            list: a list of tuples containing the selected data.
                or
            None: if no data is found.

        Examples:
            >>> _select(table_name='users', columns=('username', 'email'), condition="id=1")
            [('john_doe', 'john_doe@exmaple.com')]
        """
        # base query
        sql_query = f"SELECT {', '.join(columns)} FROM {table_name}"

        if kwargs.get('condition', None):
            sql_query += f" WHERE {kwargs.get('condition')}"
        if kwargs.get('order_by', None):
            sql_query += f" ORDER BY {kwargs.get('order_by')}"
        if kwargs.get('limit', None):
            sql_query += f" LIMIT {kwargs.get('limit')}"

        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            response = cursor.fetchall()
        self.close_connection(conn)
        return response if response else None

    @reconnect_on_exception
    def _update(self, table_name: str = None, values: str = None, condition: str = None) -> None:
        """
        Update the specified table with the given values of values based on the specified condition.

        Args:
            table_name (str): The name of the table to update.
            values (str): The values of values to update in the table.
            condition (str): The condition to use for updating the table.

        Examples:
            >>> _update('users', "username='new_username', password='new_password'", "id=1")
        """
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"UPDATE {table_name} SET {values} WHERE {condition}")
        conn.commit()
        self.close_connection(conn)

    @reconnect_on_exception
    def _delete(self, table_name: str = None, condition: str = None) -> None:
        """
        Delete rows from a table based on a condition.

        Args:
            table_name (str): The name of the table to delete rows from.
            condition (str): The condition to use to determine which rows to delete.

        Examples:
            To delete all rows from the 'users' table where the 'username' column is 'john':
            >>> db._delete('users', "username='john'")
        """
        conn = self.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name} WHERE {condition}")
        conn.commit()
        self.close_connection(conn)

    def keep_message(self, message_id: str = None, chat_id: str = None, message_content: Union[str, dict] = None, **kwargs) -> str:
        """
        Add a message to the messages table in the database.
        It is used to store the last message sent to the user for updating the message in the future.

        Args:
            message_id (str): The ID of the message.
            chat_id (str): The ID of the chat.
            message_content (Union[str, dict]): The content of the message.

        Keyword Args:
            message_type (str): The type of the message.
            state (str): The state of the message.
            recreated (bool): A flag indicating whether the message was recreated.

        Returns:
            str: A message indicating that the message was added to the messages table.

        Examples:
            >>> keep_message('12345', '67890', 'Hello, World!', message_type='status_message', state='updated')
            '12345 kept' or '12345 updated'
        """
        message_type = kwargs.get('message_type', None)
        state = kwargs.get('state', 'updated')
        recreated = kwargs.get('recreated', False)
        message_content_hash = get_hash(message_content)
        check_exist_message_type = self._select(
            table_name='messages',
            columns=("id", "message_id"),
            condition=f"message_type = '{message_type}' AND chat_id = '{chat_id}'",
        )
        response = None

        if check_exist_message_type and recreated:
            self._update(
                table_name='messages',
                values=(
                    f"message_content_hash = '{message_content_hash}', "
                    f"message_id = '{message_id}', "
                    f"state = '{state}', "
                    "updated_at = CURRENT_TIMESTAMP, "
                    "created_at = CURRENT_TIMESTAMP"
                ),
                condition=f"id = '{check_exist_message_type[0][0]}'"
            )
            response = f"{message_id} recreated"

        elif check_exist_message_type and not recreated:
            self._update(
                table_name='messages',
                values=(
                    f"message_content_hash = '{message_content_hash}', "
                    f"message_id = '{message_id}', "
                    f"state = '{state}', "
                    f"updated_at = CURRENT_TIMESTAMP"
                ),
                condition=f"id = '{check_exist_message_type[0][0]}'"
            )
            response = f"{message_id} updated"

        elif not check_exist_message_type:
            self._insert(
                table_name='messages',
                columns=("message_id", "chat_id", "message_type", "message_content_hash", "producer"),
                values=(message_id, chat_id, message_type, message_content_hash, 'bot')
            )
            response = f"{message_id} kept"

        else:
            log.warning('[Database]: Message with ID %s already exists in the messages table and cannot be updated', message_id)
            response = f"{message_id} already exists"

        return response

    def get_users(self, only_allowed: bool = True) -> dict:
        """
        This method will be deprecated after https://github.com/obervinov/users-package/issues/44 (users-package:v3.1.0).
        Get a dictionary of all users with their metadata from the users table in the database.
        By default, the method returns only allowed users.

        Args:
            only_allowed (bool): A flag indicating whether to return only allowed users. Default is True.

        Returns:
            dict: A dictionary containing all users in the database and their metadata.

        Examples:
            >>> get_users()
            [{'user_id': '12345', 'chat_id': '67890', 'status': 'denied'}, {'user_id': '12346', 'chat_id': '67891', 'status': 'allowed'}]
        """
        users_dict = []
        if only_allowed:
            users = self._select(
                table_name='users',
                columns=("user_id", "chat_id", "status"),
                condition="status = 'allowed'",
                limit=1000
            )
        else:
            users = self._select(
                table_name='users',
                columns=("user_id", "chat_id", "status"),
                limit=1000
            )

        if users:
            for user in users:
                users_dict.append({'user_id': user[0], 'chat_id': user[1], 'status': user[2]})
        return users_dict

    def get_considered_message(self, message_type: str = None, chat_id: str = None) -> tuple:
        """
        Get a message with specified type and chat ID from the messages table in the database.

        Args:
            message_type (str): The type of the message.
            chat_id (str): The ID of the chat.

        Returns:
            tuple: A tuple containing the message from the messages table.

        Examples:
            >>> current_message_id(message_type='status_message', chat_id='12345')
            # ('message_id', 'chat_id', 'created_at', 'updated_at', 'message_content_hash', 'state')
            ('123456789', '12345', datetime.datetime, datetime.datetime, 'hash', 'updated')
        """
        message = self._select(
            table_name='messages',
            columns=("message_id", "chat_id", "created_at", "updated_at", "message_content_hash", "state"),
            condition=f"message_type = '{message_type}' AND chat_id = '{chat_id}'",
            limit=1
        )
        return message[0] if message else None

    def get_finance_currency(self) -> dict:
        """
        Get the all currencies from the database for finance module.

        Returns:
            dict: A dictionary containing the currencies.

        Examples:
            >>> get_currencies()
            [{'code': 'USD', 'name': 'United States Dollar', 'rate': 1.0, 'last_update': datetime.datetime}]
        """
        currencies = []
        response = self._select(table_name='finance_currency', columns=('code', 'name', 'rate', 'last_update'))
        if response:
            for currency in response:
                currencies.append({'code': currency[0], 'name': currency[1], 'rate': currency[2], 'last_update': currency[3]})
        return currencies

    def update_finance_currency(self, currency_list: dict = None, currency_rate: dict = None) -> None:
        """
        Update the currency list or currency rate in the database for finance module.

        Args (one of the two arguments must be provided)
            currency_list (dict): A dictionary containing the currency codes and names.
            currency_rate (dict): A dictionary containing the currency codes and rates.

        Examples:
            >>> update_finance_currency(currency_list={'USD': 'United States Dollar', 'EUR': 'Euro'})
            >>> update_finance_currency(currency_rate={'USD': 1.0, 'EUR': 0.85})
        """
        if currency_list and currency_rate:
            log.error('[Finance.Currency] The currency list and rate cannot be updated at the same time.')
            raise ValueError('The currency list and rate cannot be updated at the same time.')

        if currency_list:
            exist_list = self.get_finance_currency()
            for key, value in currency_list.items():
                if key not in [currency['code'] for currency in exist_list]:
                    self._insert(
                        table_name='finance_currency',
                        columns=('code', 'name'),
                        values=(key, value)
                    )
        elif currency_rate:
            for key, value in currency_rate.items():
                self._update(table_name='finance_currency', values=f"rate={value}", condition=f"code='{key}'")
        else:
            log.error('[Finance.Currency] The currency list or rate must be provided.')
            raise ValueError('The currency list or rate must be provided.')

    def get_finance_income(self, user_id: str = None, income_name: str = None) -> dict:
        """
        Get the income from the database for finance module.

        Args:
            user_id (str): The ID of the user.
            income_name (str): The name of the income.

        Returns:
            dict: A dictionary containing the income data.

        Examples:
            >>> get_finance_income(user_id='12345', 'income_name='Salary')
            {
              'name': 'Salary', 'description': 'Salary for the month', 'category': 'Salary',
              'currency': 'USD', 'amount': 1000, 'updated_at': datetime.datetime, 'extra_data': None
            }
        """
        response = self._select(
            table_name='finance_income',
            columns=('name', 'description', 'category', 'currency', 'amount', 'updated_at', 'extra_data'),
            condition=f"name = '{income_name}' AND user_id = '{user_id}'",
            limit=1
        )
        return {
            'name': response[0][0], 'description': response[0][1], 'category': response[0][2], 'currency': response[0][3],
            'amount': response[0][4], 'updated_at': response[0][5], 'extra_data': response[0][6]
        } if response else None

    def add_finance_income(self, user_id: str = None, data: dict = None) -> None:
        """
        Add or update the income to the database for finance module.

        Args:
            user_id (str): The ID of the user.
            data (dict): A dictionary containing the income data.
                name (str): unique name of the income. Required.
                description (str): the description of the income. Required.
                category (str): the category of the income. Required.
                currency (str): the currency of the income. Required.
                amount (float): the amount of the income. Required.
                updated_at (str): the updated date of the income. Optional.
                extra_data (dict): the extra data of the income. Optional. Used for Deposit models.

        Examples:
            >>> add_finance_income(user_id='12345', name='Salary', description='Salary for the month', category='Salary', currency='USD', amount=1000)
        """
        required_fields = ('name', 'description', 'category', 'currency', 'amount')

        if not all(field in data for field in required_fields) or not user_id:
            log.error('[Database]: The required fields are missing for the Finance Income.')
            raise ValueError('The required fields are missing for the Finance Income.')

        self._insert(table_name='finance_income', columns=tuple(['user_id', *data.keys()]), values=(user_id, *data.values()))
