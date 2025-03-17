"""
This module contains the main code for the bot to work and contains the main logic linking the additional modules.
"""
import threading
import time

# from mock import MagicMock
from logger import log
from telegram import TelegramBot, exceptions as TelegramExceptions
from users import Users
from vault import VaultClient
from configs.constants import (TELEGRAM_BOT_NAME, ROLES_MAP, METRICS_PORT, METRICS_INTERVAL, VAULT_DB_ROLE)
from modules.database import DatabaseClient
# from modules.tools import get_hash
from modules.metrics import Metrics


# Vault client
vault = VaultClient()
# Telegram instance
tg = TelegramBot(vault=vault)
# Telegram bot for decorators
bot = tg.telegram_bot
# Client for communication with the database
database = DatabaseClient(vault=vault, db_role=VAULT_DB_ROLE)
# Metrics exporter
metrics = Metrics(port=METRICS_PORT, interval=METRICS_INTERVAL, metrics_prefix=TELEGRAM_BOT_NAME, vault=vault, database=database)
# Users manager instance
users = Users(vault={'instance': vault, 'role': f"{VAULT_DB_ROLE}-users"}, rate_limits=False)


# START HANDLERS BLOCK ##############################################################################################################
# Command handler for START command
@bot.message_handler(commands=['start'])
@users.access_control(flow='auth')
def start_command(message: tg.telegram_types.Message = None) -> None:
    """
    Sends a startup message to the specified Telegram chat.

    Args:
        message (telegram.telegram_types.Message): The message object containing information about the chat.
    """
    log.info('[Bot]: Processing start command for user %s...', message.chat.id)
    # Main pinned message
    reply_markup = tg.create_inline_markup(ROLES_MAP.keys())
    start_message = tg.send_styled_message(
        chat_id=message.chat.id,
        messages_template={
            'alias': 'start_message',
            'kwargs': {'username': message.from_user.username, 'userid': message.chat.id}
        },
        reply_markup=reply_markup
    )
    bot.pin_chat_message(start_message.chat.id, start_message.id)
    bot.delete_message(message.chat.id, message.id)


# Callback query handler for InlineKeyboardButton (BUTTONS)
@bot.callback_query_handler(func=lambda call: True)
@users.access_control(flow='auth')
def bot_callback_query_handler(call: tg.callback_query = None) -> None:
    """
    The handler for the callback query from the user. Mainly used to handle button presses.

    Args:
        call (telegram.callback_query): The callback query object.
    """
    log.info('[Bot]: Processing button %s for user %s...', call.data, call.message.chat.id)

    # if call.data == "Finances":
    #     help_message = tg.send_styled_message(
    #         chat_id=call.message.chat.id,
    #         messages_template={'alias': 'help_for_finances'}
    #     )
    #     bot.register_next_step_handler(call.message, finances_entrypoint, help_message)

    # else:
    #     log.error('[Bot]: Handler for button %s not found', call.data)


# Handler for incorrect flow (UNKNOWN INPUT)
@bot.message_handler(regexp=r'.*')
@users.access_control(flow='auth')
def unknown_command(message: tg.telegram_types.Message = None) -> None:
    """
    Sends a message to the user if the command is not recognized.

    Args:
        message (telegram.telegram_types.Message): The message object containing the unrecognized command.
    """
    log.error('[Bot]: Invalid command %s from user %s', message.text, message.chat.id)
    tg.send_styled_message(chat_id=message.chat.id, messages_template={'alias': 'unknown_command'})
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
            tg.launch_bot()
        except TelegramExceptions.FailedToCreateInstance as telegram_api_exception:
            log.error('[Bot]: main thread failed, restart thread: %s', telegram_api_exception)
            time.sleep(5)


if __name__ == "__main__":
    main()
