""" To do:
set inline? https://core.telegram.org/bots/inline

Possible problems:
If a user changes their Telegram name


"""

import logging
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters
from telegram import Update, ForceReply
import gsheet
from datetime import datetime
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hi {user.first_name}!")
    """
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )
    """


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update: Update, context: CallbackContext):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.effective_user.first_name)


def expenses_list(update: Update, context: CallbackContext):
    table = gsheet.print_track_list()
    context.bot.send_message(chat_id=update.effective_chat.id, text=table)


def add_item(update: Update, context: CallbackContext):
    date = datetime.today().strftime('%Y-%m-%d')
    payer = update.effective_user.first_name
    item = context.args[0]
    cost = context.args[1]
    beneficiary = context.args[2]
    gsheet.add_item(date, payer, item, cost, beneficiary)


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main():

    with open("credentials-telegram.json", "r") as read_file:
        telegram_data = json.load(read_file)

    # Create the Updater and pass it your bot's token.
    updater = Updater(telegram_data['token'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    caps_handler = CommandHandler('caps', caps)
    dispatcher.add_handler(caps_handler)

    expenses_list_handler = CommandHandler('list', expenses_list)
    dispatcher.add_handler(expenses_list_handler)

    add_item_handler = CommandHandler('add', add_item)
    dispatcher.add_handler(add_item_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)  # This handler must be added last

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

"""
bot = telegram.Bot(token='5139701208:AAHu8HR5qYqJkO8axKGecqNrPRMkYTnAoV8')

print(bot.get_me())

bot.send_message(text='Beep Boop', chat_id='-644278874')

updates = bot.get_updates()

print(updates[0])
"""
