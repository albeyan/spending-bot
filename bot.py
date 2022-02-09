""" To do:
set inline? https://core.telegram.org/bots/inline

Possible problems:
If a user changes their Telegram name


"""


import logging
import gsheet
import json
from datetime import datetime, timedelta
import imgkit
from html2image import Html2Image

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ForceReply, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# def start(update: Update, context: CallbackContext):
#     user = update.effective_user
#     context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hi {user.first_name}!")
#     # comment this below
#     update.message.reply_markdown_v2(
#         fr'Hi {user.mention_markdown_v2()}\!',
#         reply_markup=ForceReply(selective=True),
#     )
    

# def echo(update: Update, context: CallbackContext):
#     context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update: Update, context: CallbackContext):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.effective_user.first_name)


def last(update: Update, context: CallbackContext):
    # table = gsheet.print_track_list()
    # context.bot.send_message(chat_id=update.effective_chat.id, text=table, parse_mode='HTML')
    table = gsheet.get_data()
    # update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
    
    # img = imgkit.from_string(f'<pre>{table}</pre>', False, 'out.jpg')

    hti = Html2Image()
    hti.screenshot(html_str=f'<pre>{table}</pre>', save_as='img.png', size=(449, 222))
    update.message.reply_photo(photo=open('img.png', 'rb'))

    # update.message.reply_photo(photo=open('out.jpg', 'rb'))


# Adds item with text
def add_quick(update: Update, context: CallbackContext):
    date = datetime.today().strftime('%Y-%m-%d')
    payer = update.effective_user.first_name
    item = context.args[0]
    cost = context.args[1]
    beneficiary = context.args[2]
    gsheet.add_item(date, payer, item, cost, beneficiary)


DATE, PAYER, ITEM, COST, BENEFICIARY = range(5)


def add_item(update: Update, context: CallbackContext) -> int:
    """Starts by asking the date of the expense"""
    reply_keyboard = [['Today', 'Yesterday']]

    update.message.reply_text(
        'Insert the date of the expense in yyyy-mm-dd.\n\n'
        'Send /cancel to stop.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='yyyy-mm-dd'
        ),
    )

    return DATE


def date(update: Update, context: CallbackContext) -> int:
    """Stores the date and asks for payer"""
    response = update.message.text
    today = datetime.today().strftime('%Y-%m-%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    if response == 'Today':
        date = today
    elif response == 'Yesterday':
        date = yesterday
    else:
        date = response

    logger.info("Date of expense: %s", date)
    context.user_data["item"] = {}
    context.user_data["item"]["date"] = date

    reply_keyboard = [['Her', 'Isa']]

    update.message.reply_text(
        'Who paid?',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return PAYER


def payer(update: Update, context: CallbackContext) -> int:
    """Stores the payer and asks for the item name."""
    response = update.message.text

    logger.info("Payer: %s", response)
    context.user_data["item"]["payer"] = response

    update.message.reply_text('Insert the item name.')

    return ITEM


def item(update: Update, context: CallbackContext) -> int:
    """Stores the item name and asks for the cost."""
    response = update.message.text.title()

    logger.info("Item name: %s", response)
    context.user_data["item"]["name"] = response

    update.message.reply_text('Insert the cost.')

    return COST


def cost(update: Update, context: CallbackContext) -> int:
    """Stores the cost and asks for the beneficiary"""
    response = update.message.text

    logger.info("Cost: %s", response)
    context.user_data["item"]["cost"] = response

    reply_keyboard = [['Her', 'Both', 'Isa']]

    update.message.reply_text(
        'Who is this for? Both means 50/50.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return BENEFICIARY


def beneficiary(update: Update, context: CallbackContext) -> int:
    """Stores the beneficiary and ends the conversation."""
    response = update.message.text

    logger.info("Beneficiary: %s", response)
    context.user_data["item"]["beneficiary"] = response

    update.message.reply_text('Item saved!')
    logger.info("Item saved!")
    logger.info(context.user_data["item"])

    date = context.user_data["item"]["date"]
    payer = context.user_data["item"]["payer"]
    item = context.user_data["item"]["name"]
    cost = context.user_data["item"]["cost"]
    beneficiary = context.user_data["item"]["beneficiary"]
    gsheet.add_item(date, payer, item, cost, beneficiary)

    context.user_data["item"] = {}

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    context.user_data["item"] = {}
    update.message.reply_text(
        'Cancelled.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def invalid_text(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid option.")


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main():

    with open("credentials-telegram.json", "r") as read_file:
        telegram_data = json.load(read_file)

    # Create the Updater and pass it your bot's token.
    updater = Updater(telegram_data['token'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    caps_handler = CommandHandler('caps', caps)
    dispatcher.add_handler(caps_handler)

    add_quick_handler = CommandHandler('add', add_quick)
    dispatcher.add_handler(add_quick_handler)
    
    expenses_list_handler = CommandHandler('last', last)
    dispatcher.add_handler(expenses_list_handler)

# Conversation handler for adding items with full options
    payer_regex = '^(Her|Isa)$'
    date_regex = ''
    beneficiary_regex = '^(Her|Isa|Both)$'
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_item', add_item)],
        states={
            DATE: [MessageHandler(Filters.text, date)],
            PAYER: [MessageHandler(Filters.regex(payer_regex), payer)],
            ITEM: [MessageHandler(Filters.text, item)],
            COST: [MessageHandler(Filters.text, cost)],
            BENEFICIARY: [MessageHandler(Filters.regex(beneficiary_regex) & ~Filters.command, beneficiary)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    invalid_text_handler = MessageHandler(Filters.text, invalid_text)
    dispatcher.add_handler(invalid_text_handler)  # This handler must be added last

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)  # This handler must be added last

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()