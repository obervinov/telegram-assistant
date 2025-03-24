"""This module contains the class that represents the income entity."""
from logger import log


class Income:
    """
    This class represents the income entity.
    Supported model of income:
    - Salary
    - Deposit
    - CoinBox

    Attributes:


    Methods:


    Raises:

    """
    def __init__(self, database: object = None) -> None:
        """
        Initialize the class with the necessary parameters.

        Args:
            database (object): instance of the Database class.

        Examples:
            >>> Income(database=<DatabaseClient>)
        """
        self.database = database

    def _check_model(self, **kwargs) -> bool:
        """
        The method checks the model and the required fields for the income.

        Returns:
            bool: True if the model is correct, False otherwise.
        """
        required_fields = ['description', 'currency', 'amount', 'name', 'category']
        deposit_required_payload_fields = ['start_date', 'expiration_date', 'interest_rate', 'tax']

        for field in required_fields:
            if field not in kwargs:
                log.error(f'[Finance.Income] The field {field} is required for the income.')
                return False

        if not ('Salary' or 'Deposit' or 'CoinBox') in kwargs.get('category'):
            log.error(f'[Finance.Income] The model {kwargs.get("category")} is not supported.')
            return False

        if kwargs.get('category') == 'Deposit':
            for field in deposit_required_payload_fields:
                if field not in kwargs:
                    log.error(f'[Finance.Income] The field {field} is required for the deposit model.')
                    return False

        return True

    def _check_income_exists(self, name) -> bool:
        """
        The method checks if the income already exists in the database.

        Args:
            name (str): the name of the income.

        Returns:
            bool: True if the income exists, False otherwise.
        """
        if self.database.get_income(name=name):
            log.error(f'[Finance.Income] The income with name {name} already exists in the database.')
            return True
        return False

    def income(self, name: str, **payload) -> None:
        """
        The method add or update the income to the database. Supported:
         - Salary - a simple basic income accounting model without regular changes.
         - Deposit - a model for automatic accounting and updating of the deposit amount, taking into account interest charges and the final tax.
         - CoinBox - a model for accounting for the amount of coins in the box. Supported simple increase and decrease of the amount.

        Args:
            name (str): unique name of the income. Required.
            **payload: the additional fields for the income.

        Keyword Args:
            (used for all models):
                description (str): the description of the income.
                category (str): the category of the income.
                currency (str): the currency of the income.
                amount (float): the amount of the income.
            model Deposit (payload fields):
                :param start_date (str): the start date of the deposit.
                :param expiration_date (str): the expiration date of the deposit.
                :param interest_rate (float): the interest rate of the deposit (in percent).
                :param tax (float): the tax of the deposit (in percent).
        Examples:
            >>> income(category='Salary', name='Salary', description='Salary for the month', currency='USD', amount=1000)
            >>> income(category='CoinBox', name='CoinBox', description='CoinBox for the month', currency='USD', amount=1000)
            >>> income(
            >>>   category='Deposit', name='Deposit', description='Deposit for the month', currency='USD', amount=1000,
            >>>   start_date='2021-01-01', expiration_date='2022-01-01', interest_rate=2, tax=10
            >>> )
        """
        if self._check_model(name=name, **payload):
            if not self._check_income_exists(name=name):
                log.info(f'[Finance.Income] Adding the new income with name {name} to the database...')
                income_dict = {
                    'name': name, 'description': payload.get('description'), 'category': payload.get('category'), 'currency': payload.get('currency'),
                    'amount': payload.get('amount'), 'extra_data': payload.get('extra_data', None)
                }
                self.database.add_finance_income(**income_dict)
            else:
                log.info(f'[Finance.Income] Updating the income with name {self.name} in the database...')
                self.database.update_income(name=self.name, model=self.model, data=self.data)

    # def watcher(self) -> None:
    #     """
    #     Method for running the income background task as a separate thread.
    #     """
    #     log.info('[Finance.Income]: Running the watcher for the background task...')
    #     while True:
    #         pass
