"""
This module contains custom exceptions that are used in the application.
"""


class WrongVaultInstance(Exception):
    """
    Exception raised when the vault instance is not correct.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
