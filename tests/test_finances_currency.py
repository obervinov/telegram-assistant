"""Tests for the Currency sub module of the finance module."""
from decimal import Decimal
import pytest


@pytest.mark.order(5)
def test_get_currency_from_database(finance_currency_instance):
    """
    Checking the method for getting currencies from the exchange API.
    """
    data = []
    finance_currency_instance.update_currency_cache()
    for item in finance_currency_instance.get_currency():
        item.pop('last_update')
        data.append(item)
    assert data == [
        {'code': 'USD', 'name': 'United States Dollar', 'rate': Decimal('1.00')},
        {'code': 'EUR', 'name': 'Euro', 'rate': Decimal('0.85')},
        {'code': 'GBP', 'name': 'British Pound Sterling', 'rate': Decimal('0.75')},
    ]


@pytest.mark.order(6)
def test_currency_converter(finance_currency_instance):
    """
    Checking the method for converting currency.
    """
    finance_currency_instance.update_currency_cache()
    assert finance_currency_instance.currency_converter('USD', 100, 'EUR') == 85.0
