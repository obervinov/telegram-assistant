"""Tests for the currency sub module of the finance module."""
import re
import pytest
from decimal import Decimal


@pytest.mark.order(5)
def test_get_currencies_from_database(currency_instance):
    """
    Checking the method for getting currencies from the exchange API.
    """
    currency_instance.update_currencies_cache()
    response = currency_instance.get_currencies().pop('last_update')
    assert response == [
        {'code': 'USD', 'name': 'United States Dollar', 'rate': Decimal('1.00')},
        {'code': 'EUR', 'name': 'Euro', 'rate': Decimal('0.85')},
        {'code': 'GBP', 'name': 'British Pound Sterling', 'rate': Decimal('0.73')},
    ]


@pytest.mark.order(6)
def test_currency_converter(currency_instance):
    """
    Checking the method for converting currency.
    """
    currency_instance.update_currencies_cache()
    assert currency_instance.currency_converter('USD', 100, 'EUR') == 85.0
