"""
This module contains custom exceptions that are used in the finance module.
"""


class FailedExchangeAPIRequest(Exception):
    """
    Exception raised when the exchange API request fails.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class WrongVaultConfiguration(Exception):
    """
    Exception raised when the vault configuration is not valid.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
