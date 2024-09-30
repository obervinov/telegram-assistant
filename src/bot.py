"""
This module contains the main code for the bot to work and contains the main logic linking the additional modules.
"""
from datetime import datetime, timedelta
import re
import threading
import time
import random
import string

from mock import MagicMock
from logger import log
from telegram import TelegramBot, exceptions as TelegramExceptions
from users import Users
from vault import VaultClient
from configs.constants import (
    TELEGRAM_BOT_NAME, ROLES_MAP,
    METRICS_PORT, METRICS_INTERVAL,
    VAULT_DBENGINE_MOUNT_POINT, VAULT_DB_ROLE_MAIN, VAULT_DB_ROLE_USERS
)
from modules.database import DatabaseClient
from modules.tools import get_hash
from modules.metrics import Metrics


# Vault client
# The need to explicitly specify a mount point will no longer be necessary after solving the https://github.com/obervinov/vault-package/issues/49
vault = VaultClient(dbengine={"mount_point": VAULT_DBENGINE_MOUNT_POINT})
# Telegram instance
telegram = TelegramBot(vault=vault)
# Telegram bot for decorators
bot = telegram.telegram_bot
# Users module without rate limits option
users = Users(vault=vault, storage={'db_role': VAULT_DB_ROLE_USERS})

# Client for communication with the database
database = DatabaseClient(vault=vault, db_role=VAULT_DB_ROLE_MAIN)

# Metrics exporter
metrics = Metrics(port=METRICS_PORT, interval=METRICS_INTERVAL, metrics_prefix=TELEGRAM_BOT_NAME, vault=vault, database=database)


# START HANDLERS BLOCK ##############################################################################################################
# Command handler for START command
@bot.message_handler(commands=['start'])
def start_command(message: telegram.telegram_types.Message = None) -> None:
    """
    Sends a startup message to the specified Telegram chat.

    Args:
        message (telegram.telegram_types.Message): The message object containing information about the chat.
    """
    requestor = {'user_id': message.chat.id, 'chat_id': message.chat.id, 'message_id': message.message_id}
    if users.user_access_check(**requestor).get('access', None) == users.user_status_allow:
        log.info('[Bot]: Processing start command for user %s...', message.chat.id)
        # Main pinned message
        reply_markup = telegram.create_inline_markup(ROLES_MAP.keys())
        start_message = telegram.send_styled_message(
            chat_id=message.chat.id,
            messages_template={
                'alias': 'start_message',
                'kwargs': {'username': message.from_user.username, 'userid': message.chat.id}
            },
            reply_markup=reply_markup
        )
        bot.pin_chat_message(start_message.chat.id, start_message.id)
        bot.delete_message(message.chat.id, message.id)
        update_status_message(user_id=message.chat.id)
    else:
        telegram.send_styled_message(
            chat_id=message.chat.id,
            messages_template={
                'alias': 'reject_message',
                'kwargs': {'username': message.chat.username, 'userid': message.chat.id}
            }
        )


# Callback query handler for InlineKeyboardButton (BUTTONS)
@bot.callback_query_handler(func=lambda call: True)
def bot_callback_query_handler(call: telegram.callback_query = None) -> None:
    """
    The handler for the callback query from the user.
    Mainly used to handle button presses.

    Args:
        call (telegram.callback_query): The callback query object.
    """
    log.info('[Bot]: Processing button %s for user %s...', call.data, call.message.chat.id)
    requestor = {
        'user_id': call.message.chat.id, 'role_id': ROLES_MAP[call.data],
        'chat_id': call.message.chat.id, 'message_id': call.message.message_id
    }
    if users.user_access_check(**requestor).get('permissions', None) == users.user_status_allow:
        if call.data == "Finances":
            help_message = telegram.send_styled_message(
                chat_id=call.message.chat.id,
                messages_template={'alias': 'help_for_finances'}
            )
            bot.register_next_step_handler(call.message, finances_entrypoint, help_message)

        elif call.data == "Goals":
            help_message = telegram.send_styled_message(
                chat_id=call.message.chat.id,
                messages_template={'alias': 'help_for_goals'}
            )
            bot.register_next_step_handler(call.message, goals_entrypoint, help_message)

        else:
            log.error('[Bot]: Handler for button %s not found', call.data)

    else:
        telegram.send_styled_message(
            chat_id=call.message.chat.id,
            messages_template={
                'alias': 'permission_denied_message',
                'kwargs': {'username': call.message.chat.username, 'userid': call.message.chat.id}
            }
        )


# Handler for incorrect flow (UNKNOWN INPUT)
@bot.message_handler(regexp=r'.*')
def unknown_command(message: telegram.telegram_types.Message = None) -> None:
    """
    Sends a message to the user if the command is not recognized.

    Args:
        message (telegram.telegram_types.Message): The message object containing the unrecognized command.
    """
    requestor = {'user_id': message.chat.id, 'chat_id': message.chat.id, 'message_id': message.message_id}
    if users.user_access_check(**requestor).get('access', None) == users.user_status_allow:
        log.error('[Bot]: Invalid command %s from user %s', message.text, message.chat.id)
        telegram.send_styled_message(chat_id=message.chat.id, messages_template={'alias': 'unknown_command'})
    else:
        telegram.send_styled_message(
            chat_id=message.chat.id,
            messages_template={
                'alias': 'reject_message',
                'kwargs': {'username': message.chat.username, 'userid': message.chat.id}
            }
        )
# END HANDLERS BLOCK ##############################################################################################################


def main():
    """
    The main entry point of the project.

    Args:
        None

    Returns:
        None
    """
    # Thread for export metrics
    threads = threading.enumerate()
    thread_metrics = threading.Thread(target=metrics.run, args=(threads,), name="MetricsThread")
    thread_metrics.start()
    # Run bot
    while True:
        try:
            telegram.launch_bot()
        except TelegramExceptions.FailedToCreateInstance as telegram_api_exception:
            log.error('[Bot]: main thread failed, restart thread: %s', telegram_api_exception)
            time.sleep(5)


if __name__ == "__main__":
    main()
