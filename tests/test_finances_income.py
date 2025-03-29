"""Tests for the Income sub module of the finance module."""
import pytest


@pytest.mark.order(7)
def test_add_income_to_database(finance_income_instance, database_class):
    """
    Checking the method for adding income to the database.
    """
    salary_data = {'name': 'Salary', 'description': 'Main income', 'category': 'Salary', 'currency': 'USD', 'amount': 1000}
    coinbox_data = {'name': 'CoinBox', 'description': 'Additional income', 'category': 'CoinBox', 'currency': 'USD', 'amount': 500}
    deposit_data = {
        'name': 'Deposit', 'description': 'Passive income', 'category': 'Deposit', 'currency': 'USD', 'amount': 1000,
        'start_date': '2021-01-01', 'expiration_date': '2022-01-01', 'interest_rate': 10, 'tax': 5
    }
    finance_income_instance.income(user_id='111', **salary_data)
    finance_income_instance.income(user_id='111', **coinbox_data)
    finance_income_instance.income(user_id='111', **deposit_data)

    db_salary_data = database_class.get_finance_income(user_id='111', income_name='Salary')
    db_coinbox_data = database_class.get_finance_income(user_id='111', income_name='CoinBox')
    # db_deposit_data = database_class.get_finance_income(income_name='Deposit')

    assert db_salary_data is not None
    assert db_coinbox_data is not None
    # assert db_deposit_data is not

    assert db_salary_data.pop('updated_at').pop('extra_data') == salary_data
    assert db_coinbox_data.pop('updated_at').pop('extra_data') == coinbox_data
    # assert db_deposit_data.pop('updated_at') == deposit_data['extra_data'
