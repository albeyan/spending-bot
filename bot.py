""" To do:
Possible problems:
If a user changes their Telegram name
"""
import os
import logging
import gsheet
import json
from datetime import datetime, timedelta
from html2image import Html2Image
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

PLAYER_1 = os.environ["PLAYER_1"]
PLAYER_2 = os.environ["PLAYER_2"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
BROWSER_PATH = os.environ["GOOGLE_CHROME_SHIM"]  # Change to GOOGLE_CHROME_BIN in local env

DATE, PAYER, ITEM, COST, BENEFICIARY = range(5)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def get_debt(update: Update, context: CallbackContext):
    debt = gsheet.calculate_debt()
    
    if PLAYER_1 in debt.keys():
        debtor = PLAYER_1
        creditor = PLAYER_2
    elif PLAYER_2 in debt.keys():
        debtor = PLAYER_2
        creditor = PLAYER_1
    else:
        update.message.reply_text('Nobody owes money.')
        return

    response = f"{debtor} owes {debt[debtor]} to {creditor}" 
    update.message.reply_text(response)


def settle_debt(update: Update, context: CallbackContext):
    debt = gsheet.calculate_debt()

    if PLAYER_1 in debt.keys():
        payer = PLAYER_1
        beneficiary = PLAYER_2
    elif PLAYER_2 in debt.keys():
        payer = PLAYER_2
        beneficiary = PLAYER_1
    else:
        update.message.reply_text("There's no debt to settle.")
        return
    
    date = datetime.today().strftime('%Y-%m-%d')
    item = 'Deuda'
    cost = debt[payer]
    gsheet.add_item(date, payer, item, cost, beneficiary)
    update.message.reply_text(f"{payer} has paid {cost} to {beneficiary}.")


def last(update: Update, context: CallbackContext):
    table = gsheet.print_last_items()
    hti = Html2Image(browser_executable=BROWSER_PATH)
    hti.screenshot(html_str=f'<pre>{table}</pre>',
                    save_as='tmp/img.png', size=(522, 222))
    update.message.reply_photo(photo=open('tmp/img.png', 'rb'))


def delete_item(update: Update, context: CallbackContext):
    if len(context.args) == 1:
        id = context.args[0]
        gsheet.delete_item(id)
        update.message.reply_text('Item deleted.')
    else:
        update.message.reply_text('Usage: "/delete 14"\n\n'
                                + 'No item was deleted.')


def delete_last(update: Update, context: CallbackContext):
    gsheet.delete_last()
    update.message.reply_text('The last item was deleted.')


# Adds item with text
def add_quick(update: Update, context: CallbackContext):
    date = datetime.today().strftime('%Y-%m-%d')
    payer = update.effective_user.first_name
    item = context.args[0]
    cost = context.args[1]
    beneficiary = context.args[2]
    gsheet.add_item(date, payer, item, cost, beneficiary)


def add_item(update: Update, context: CallbackContext) -> int:
    """Starts by asking the date of the expense"""
    reply_keyboard = [['Today', 'Yesterday']]

    update.message.reply_text(
        'Insert the date of the expense in yyyy-mm-dd.\n\n'
        'Send /cancel to stop.',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='yyyy-mm-dd'
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

    reply_keyboard = [[PLAYER_1, PLAYER_2]]

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

    reply_keyboard = [[PLAYER_1, 'Both', PLAYER_2]]

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
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text="Invalid option.")


def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                            text="Sorry, I didn't understand that command.")


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    add_quick_handler = CommandHandler('add', add_quick)
    dispatcher.add_handler(add_quick_handler)
    
    expenses_list_handler = CommandHandler('last', last)
    dispatcher.add_handler(expenses_list_handler)
    
    get_debt_handler = CommandHandler('debt', get_debt)
    dispatcher.add_handler(get_debt_handler)
    
    settle_debt_handler = CommandHandler('settle', settle_debt)
    dispatcher.add_handler(settle_debt_handler)
    
    delete_item_handler = CommandHandler('delete', delete_item)
    dispatcher.add_handler(delete_item_handler)
    
    delete_last_handler = CommandHandler('delete_last', delete_last)
    dispatcher.add_handler(delete_last_handler)

# Conversation handler for adding items with full options
    payer_regex = f'^({PLAYER_1}|{PLAYER_2})$'
    date_regex = ''
    beneficiary_regex = f'^({PLAYER_1}|{PLAYER_2}|Both)$'
    
    add_item_handler = ConversationHandler(
        entry_points=[CommandHandler('add_item', add_item)],
        states={
            DATE: [MessageHandler(Filters.text, date)],
            PAYER: [MessageHandler(Filters.regex(payer_regex), payer)],
            ITEM: [MessageHandler(Filters.text, item)],
            COST: [MessageHandler(Filters.text, cost)],
            BENEFICIARY: [MessageHandler(Filters.regex(beneficiary_regex)
                                        & ~Filters.command, beneficiary)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(add_item_handler)

    # This handler must be added last
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    # This handler must be added last
    invalid_text_handler = MessageHandler(Filters.text, invalid_text)
    dispatcher.add_handler(invalid_text_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
