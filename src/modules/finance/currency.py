"""This module contains the currencies module for this python project."""
from datetime import datetime
import time
import requests
from logger import log
from .exceptions import FailedExchangeAPIRequest


class Currency():
    """
    This class provides a way to get the currency exchange rates from the Open Exchange Rates API
    Source: https://openexchangerates.org

    Attributes:
        :attribute app_id (str): the APP ID for the Open Exchange Rates API.
        :attribute api_url (str): the URL of the Open Exchange Rates API.
        :attribute frequency (int): the frequency of the API calls in hours.
        :attribute base_currency (str): the base currency for the exchange rates.
        :attribute headers (dict): the headers for the API calls.
        :attribute timeout (int): the timeout for the API calls.
        :attribute database (Database): instance of the Database class.

    Methods:
        :method _get_finance_currencies_from_api(): Get the currencies from the Open Exchange Rates API. Private method.
        :method _get_exchange_rates_from_api(): Get the exchange rates from the Open Exchange Rates API. Private method.
        :method get_finance_currencies(): Get the currencies from the internal database.
        :method update_currencies_cache(): Update the currencies cache in the database.
        :method currency_converter(from_currency: str, amount: float, to_currency: str): Convert the amount from one currency to another.
        :method watcher(): Method for running the currency background task as a separate thread.

    Raises:
        :raises FailedExchangeAPIRequest: Raised when the exchange API request fails.
    """
    def __init__(self, app_id: str, database: object, **kwargs) -> None:
        """
        Initialize the class with the necessary parameters.

        Args:
            :param app_id (str): the APP ID for the Open Exchange Rates API (https://docs.openexchangerates.org/reference/authentication)
            :param database (Database): instance of the Database class.

        Keyword Args:
            :param api_url (str): the URL of the Open Exchange Rates API. Default is 'https://openexchangerates.org/api'.
            :param frequency (int): the frequency of the API calls in hours. Default is 24 hours.
            :param base_currency (str): the base currency for the exchange rates. Default is 'USD'.
            :param request_timeout (int): the timeout for the API calls. Default is 10 seconds.

        Examples:
            >>> Currency(app_id='your_app_id', database=<DatabaseClient>)
        """
        self.app_id = app_id
        self.database = database
        self.api_url = kwargs.get('api_url', 'https://openexchangerates.org/api')
        self.frequency = kwargs.get('frequency', 24)
        self.base_currency = kwargs.get('base_currency', 'USD')
        self.timeout = kwargs.get('request_timeout', 10)
        self.headers = {'accept': 'application/json'}

    def _get_finance_currencies_from_api(self) -> dict:
        """
        Get the currencies from the Open Exchange Rates API.

        Returns:
            dict: A dictionary containing the currencies.
        Return
        """
        url = f"{self.api_url}/currencies.json&app_id={self.app_id}"
        response = requests.get(url=url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 200:
            log.info('[Finance.Currency]: Successfully retrieved the currencies from the API.')
            return response.json()
        log.error('[Finance.Currency]: Failed to retrieve the currencies from the API: %s', response.text)
        raise FailedExchangeAPIRequest("Failed to retrieve the currencies from the API.")

    def _get_exchange_rates_from_api(self) -> dict:
        """
        Get the exchange rates from the Open Exchange Rates API.

        Returns:
            dict: A dictionary containing the exchange rates.
        """
        url = f"{self.api_url}/latest.json?app_id={self.app_id}&base={self.base_currency}&prettyprint=false&show_alternative=false"
        response = requests.get(url=url, headers=self.headers, timeout=self.timeout)
        if response.status_code == 200:
            log.info('[Finance.Currency]: Successfully retrieved the exchange rates from the API.')
            return response.json()
        log.error('[Finance.Currency]: Failed to retrieve the exchange rates from the API: %s', response.text)
        raise FailedExchangeAPIRequest("Failed to retrieve the exchange rates from the API.")

    def get_currency(self) -> dict:
        """
        Get the currencies from the database.

        Returns:
            dict: A dictionary containing the currencies.

        Examples:
            >>> get_finance_currencies()
            [{'code': 'USD', 'name': 'United States Dollar', 'rate': 1.0, 'last_update': datetime.datetime}]
        """
        log.info('[Finance.Currency]: Getting currencies from the database...')
        return self.database.get_finance_currency()

    def update_currency_cache(self) -> None:
        """
        Update the currencies cache in the database.
        """
        log.info('[Finance.Currency]: Updating the currencies cache...')
        log.info('[Finance.Currency]: Getting currencies from the exchange API...')
        currencies = self._get_finance_currencies_from_api()
        log.info('[Finance.Currency]: Getting exchange rates from the exchange API...')
        currencies_rate = self._get_exchange_rates_from_api()

        log.info('[Finance.Currency]: Updating the currencies list in the database...')
        self.database.update_finance_currency(currency_list=currencies)
        log.info('[Finance.Currency]: Updating the exchange rates in the database...')
        self.database.update_finance_currency(currency_rate=currencies_rate['rates'])

    def currency_converter(self, from_currency: str, amount: float, to_currency: str) -> float:
        """
        Convert the amount from one currency to another.

        Args:
            :param from_currency (str): the currency to convert from.
            :param amount (float): the amount to convert.
            :param to_currency (str): the currency to convert to.

        Returns:
            float: The converted amount.

        Examples:
            >>> currency_converter('USD', 100, 'EUR')
            85.0
        """
        log.info('[Finance.Currency]: Converting currency %s %s -> %s', amount, from_currency, to_currency)
        currency_cache = self.get_currency()

        if from_currency == to_currency:
            value = amount

        elif from_currency == self.base_currency:
            for currency in currency_cache:
                if currency.get('code') == to_currency:
                    value = amount * currency.get('rate', 0)

        elif to_currency == self.base_currency:
            for currency in currency_cache:
                if currency.get('code') == from_currency:
                    value = amount / currency.get('rate', 0)

        else:
            from_rate = 0.0
            to_rate = 0.0
            for currency in currency_cache:
                if currency.get('code') == from_currency:
                    from_rate = currency.get('rate', 0)
                if currency.get('code') == to_currency:
                    to_rate = currency.get('rate', 0)
            value = amount * to_rate / from_rate

        return value

    def watcher(self) -> None:
        """
        Method for running the currency background task as a separate thread.
        """
        log.info('[Finance.Currency]: Running the watcher for the background task...')
        while True:
            currency_cache = self.get_currency()
            if not currency_cache:
                self.update_currency_cache()
            elif currency_cache and (datetime.now() - currency_cache.get('last_update')).seconds > self.frequency * 3600:
                self.update_currency_cache()
            log.info('[Finance.Currency]: Currency module finished successfully.')
            time.sleep(60)
