"""Tests for the Income sub module of the finance module."""
import pytest


@pytest.mark.order(7)
def test_add_income_to_database(finance_income_instance, database_class):
    """
    Checking the method for adding income to the database.
    """
    salary_data = {'name': 'Salary', 'description': 'Main income', 'category': 'salary', 'currency': 'USD', 'amount': 1000}
    coinbox_data = {'name': 'CoinBox', 'description': 'Additional income', 'category': 'coinbox', 'currency': 'USD', 'amount': 500}
    deposit_data = {
        'name': 'Deposit', 'description': 'Passive income', 'category': 'deposit', 'currency': 'USD', 'amount': 1000,
        'extra_data': {'start_date': '2021-01-01', 'expiration_date': '2022-01-01', 'interest_rate': 10, 'tax': 5}
    }
    finance_income_instance.add(user_id='111', **salary_data)
    finance_income_instance.add(user_id='111', **coinbox_data)
    finance_income_instance.add(user_id='111', **deposit_data)

    db_salary_data = database_class.get_finance_income(user_id='111', income_name='Salary')
    db_coinbox_data = database_class.get_finance_income(user_id='111', income_name='CoinBox')
    db_deposit_data = database_class.get_finance_income(user_id='111', income_name='Deposit')

    assert db_salary_data is not None
    assert db_coinbox_data is not None
    assert db_deposit_data is not None

    db_salary_data.pop('updated_at', None)
    db_salary_data.pop('extra_data', None)
    assert db_salary_data == salary_data

    db_coinbox_data.pop('updated_at', None)
    db_coinbox_data.pop('extra_data', None)
    assert db_coinbox_data == coinbox_data

    db_deposit_data.pop('updated_at', None)
    assert db_deposit_data == deposit_data
