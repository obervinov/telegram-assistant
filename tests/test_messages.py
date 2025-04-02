"""
This module contains tests for the messages module.
"""
import pytest


@pytest.mark.order(9)
def test_messages(messages_instance):
    """
    Checking that the messages module is initialized correctly with src/configs/messages.json
    """
    assert messages_instance is not None
