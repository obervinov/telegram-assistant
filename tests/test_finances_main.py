"""Tests for the Income sub module of the finance module."""
import pytest


@pytest.mark.order(8)
def test_init_finance_module(finance_instance):
    """
    Checking the initialization of the finance module.
    """
    assert finance_instance is not None

    assert finance_instance.configuration is not None
    assert finance_instance.currency is not None
    assert finance_instance.income is not None

    assert finance_instance.configuration['currency_app_id'] == 'currency_app_id'