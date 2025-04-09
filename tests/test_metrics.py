"""
This module contains tests for the database module.
"""
import requests
import pytest


@pytest.mark.order(0)
def test_metrics_instance(metrics_class, database_class):
    """
    Checking the creation of a metrics instance.
    """
    assert metrics_class.port == 8000
    assert metrics_class.interval == 5
    assert metrics_class.database == database_class
    assert metrics_class.thread_status_gauge is not None


@pytest.mark.order(2)
def test_metrics_threads_status(metrics_class):
    """
    Checking the collection of thread statistics.
    """
    response = requests.get(f"http://0.0.0.0:{metrics_class.port}/", timeout=10)
    assert "pytest_thread_status" in response.text
    assert 'pytest_thread_status{thread_name="MainThread"} 1.0' in response.text
