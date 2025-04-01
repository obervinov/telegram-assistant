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
                log.error('[Finance.Income] The field %s is required for the income.', field)
                return False

        if kwargs.get('category') not in ['Salary', 'Deposit', 'CoinBox']:
            log.error('[Finance.Income] The category %s is not supported for the income.', kwargs.get('category'))
            return False

        if kwargs.get('category') == 'Deposit':
            for field in deposit_required_payload_fields:
                if field not in kwargs.get('extra_data', {}):
                    log.error('[Finance.Income] The field %s is required for the income.', field)
                    return False

        return True

    def _check_income_exists(self, user_id, name) -> bool:
        """
        The method checks if the income already exists in the database.

        Args:
            user_id (str): the user id of the income.
            name (str): the name of the income.

        Returns:
            bool: True if the income exists, False otherwise.
        """
        if self.database.get_finance_income(user_id=user_id, income_name=name):
            log.error('[Finance.Income] The income with name %s already exists in the database for user %s.', name, user_id)
            return True
        return False

    def income(self, user_id: str, name: str, **payload) -> None:
        """
        The method add or update the income to the database. Supported:
         - Salary - a simple basic income accounting model without regular changes.
         - Deposit - a model for automatic accounting and updating of the deposit amount, taking into account interest charges and the final tax.
         - CoinBox - a model for accounting for the amount of coins in the box. Supported simple increase and decrease of the amount.

        Args:
            user_id (str): the user id of the income.
            name (str): unique name of the income. Required.
            **payload: the additional fields for the income.

        Keyword Args (Payload fields):
            (used for all models):
                description (str): the description of the income.
                category (str): the category of the income.
                currency (str): the currency of the income.
                amount (float): the amount of the income.
            model Deposit (expected in extra_data field):
                extra_data (dict): the extra data for the income. Required for Deposit model.
                    start_date (str): the start date of the deposit.
                    expiration_date (str): the expiration date of the deposit.
                    interest_rate (float): the interest rate of the deposit.
                    tax (float): the tax of the deposit.
        Examples:
            >>> income(user_id='12345', category='Salary', name='Salary', description='Salary for the month', currency='USD', amount=1000)
            >>> income(user_id='12345', category='CoinBox', name='CoinBox', description='CoinBox for the month', currency='USD', amount=1000)
            >>> income(
            >>>   user_id='12345', category='Deposit', name='Deposit', description='Deposit for the month', currency='USD', amount=1000,
            >>>   extra_data={'start_date': '2021-01-01', 'expiration_date': '2022-01-01', 'interest_rate': 2, 'tax': 10}
            >>> )
        """
        if self._check_model(name=name, **payload):
            if not self._check_income_exists(user_id=user_id, name=name):
                log.info('[Finance.Income] Adding the income with name %s to the database...', name)
                income_dict = {
                    'name': name, 'description': payload.get('description'), 'category': payload.get('category'), 'currency': payload.get('currency'),
                    'amount': payload.get('amount'), 'extra_data': payload.get('extra_data', None)
                }
                self.database.add_finance_income(user_id=user_id, data=income_dict)
            else:
                log.info('[Finance.Income] Updating the income with name %s in the database...', name)
                # self.database.update_income(name=self.name, model=self.model, data=self.data)

    def watcher(self) -> None:
        """
        Method for running the income background task as a separate thread.
        """
        log.info('[Finance.Income]: Running the watcher for the background task...')
        while True:
            pass
