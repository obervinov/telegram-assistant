"""Tests for the Income sub module of the finance module."""
from decimal import Decimal
import pytest


@pytest.mark.order(7)
def test_add_income_to_database(finance_income_instance, postgres_instance):
    """
    Checking the method for adding income to the database.
    """
    salary_data = {'name': 'Salary', 'description': 'Main income', 'category': 'Salary', 'currency': 'USD', 'amount': 1000}
    coinbox_data = {'name': 'CoinBox', 'description': 'Additional income', 'category': 'CoinBox', 'currency': 'USD', 'amount': 500}
    deposit_data = {
        'name': 'Deposit', 'description': 'Passive income', 'category': 'Deposit', 'currency': 'USD', 'amount': 1000,
        'start_date': '2021-01-01', 'expiration_date': '2022-01-01', 'interest_rate': 10, 'tax': 5
    }
    finance_income_instance.income(**salary_data)
    finance_income_instance.income(**coinbox_data)
    finance_income_instance.income(**deposit_data)

    db_data = postgres_instance.cursor().execute('SELECT * FROM finance_income').fetchall()

    assert db_data == [
        ('Salary', 'Main income', 'Salary', 'USD', Decimal('1000.00'), None),
        ('CoinBox', 'Additional income', 'CoinBox', 'USD', Decimal('500.00'), None),
        ('Deposit', 'Passive income', 'Deposit', 'USD', Decimal('1000.00'), None)
    ]
