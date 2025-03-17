"""Tests for the currency sub module of the finance module."""
import pytest


@pytest.mark.order(5)
def test_get_currencies_from_database(currency_instance):
    """
    Checking the method for getting currencies from the exchange API.
    """
    currency_instance.update_currencies_cache()
    assert currency_instance.get_currencies() == {"USD": "United States Dollar", "EUR": "Euro", "GBP": "British Pound Sterling"}


@pytest.mark.order(6)
def test_currency_converter(currency_instance):
    """
    Checking the method for converting currency.
    """
    currency_instance.update_currencies_cache()
    assert currency_instance.currency_converter('USD', 100, 'EUR') == 85.0
