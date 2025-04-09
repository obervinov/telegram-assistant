"""
This module contains the constants for this python project.
"""
import os

# environment variables
TELEGRAM_BOT_NAME = os.environ.get('TELEGRAM_BOT_NAME', 'telegram-assistant')

# permissions roles and buttons mapping
# 'button_title': 'role'
ROLES_MAP = {
    'Finance: Income': 'finances',
    'Finance: Expenses': 'finances',
    'Finance: Report': 'finances',
    'Finance: Settings': 'finances',
}

# Other constants
STATUSES_MESSAGE_FREQUENCY = 15
METRICS_PORT = 8000
METRICS_INTERVAL = 30

# Vault Database Engine constants
VAULT_DB_ROLE = f"{TELEGRAM_BOT_NAME}"
