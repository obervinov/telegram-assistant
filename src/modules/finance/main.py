"""This module is responsible for initializing and combining all financial submodules into common entry points."""
from logger import log
from .exceptions import WrongVaultConfiguration
from .currency import Currency
from .income import Income


# pylint: disable=too-few-public-methods
class Finance:
    """
    This class represents the Finance module.
    It combines all financial submodules into a common entry point.

    Attributes:

    Methods:

    Raises:

    Vault configuration fields:
        - currency_app_id: The application ID for the currency exchange API. Required.
        - currency_app_url: The URL for the currency exchange API. Optional.
        - currency_frequency: The frequency of the currency exchange API calls in hours. Optional.
        - currency_base_currency: The base currency for the currency exchange API. Optional.
        - currency_request_timeout: The timeout for the currency exchange API calls in seconds. Optional.
    """

    def __init__(self, database: object = None, vault: object = None) -> None:
        """
        Initialize the class with the necessary parameters.

        Args:
            database (object): instance of the Database class.
            vault (object): instance of the Vault class.

        Examples:
            >>> Finance(database=<DatabaseClient>, vault=<VaultClient>)
        """
        log.info('[Finance] Initializing the finance module.')
        self.configuration = vault.kv2.read_secret(path='configuration/finance')
        currency_config = {}
        income_config = {}
        expense_config = {}

        if not self._configuration_validation():
            raise WrongVaultConfiguration(message='The vault configuration for the finance module is not valid.')

        for key, value in self.configuration.items():
            if key.startswith('currency_'):
                currency_config[key] = value
            elif key.startswith('income_'):
                income_config[key] = value
            elif key.startswith('expense_'):
                expense_config[key] = value

        log.info('[Finance] The configuration for the finance module is valid.')
        log.debug('[Finance] The configuration for the finance module is %s', self.configuration)

        self.currency = Currency(database=database, **currency_config)
        self.income = Income(database=database, **income_config)

    def _configuration_validation(self) -> bool:
        """
        The method checks the configuration for the finance module.

        Returns:
            bool: True if the configuration is correct, False otherwise.
        """
        required_fields = ['currency_app_id']

        for field in required_fields:
            if field not in self.configuration:
                log.error('[Finance] The field %s is required for the finance module.', field)
                return False

        return True

    def widget(self) -> bool:
        """
        The method checks the model and the required fields for the income.

        Returns:
            bool: True if the model is correct, False otherwise.
        """
        log.info('[Finance] The widget method is not implemented yet.')
