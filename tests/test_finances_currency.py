"""Tests for the currency sub module of the finance module."""
import pytest
import re


@pytest.mark.order(5)
def test_get_currencies_from_database(currency_instance):
    """
    Checking the method for getting currencies from the exchange API.
    """
    currency_instance.update_currencies_cache()
    assert currency_instance.get_currencies() == [
        {'code': 'USD', 'name': 'United States Dollar', 'rate': 1.00, 'last_update': re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')},
        {'code': 'EUR', 'name': 'Euro', 'rate': 0.85, 'last_update': re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')},
        {'code': 'GBP', 'name': 'British Pound Sterling', 'rate': 0.72, 'last_update': re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')}
    ]


@pytest.mark.order(6)
def test_currency_converter(currency_instance):
    """
    Checking the method for converting currency.
    """
    currency_instance.update_currencies_cache()
    assert currency_instance.currency_converter('USD', 100, 'EUR') == 85.0
