# Бот предоставляет расписание студентам УРФУ
# Bot present schedule for UrFU students

# Import
from telegram import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
import logging
from parser import schedule

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

GROUP_NUMBER = 0

# Define command for Handlers


def keyboard(button=True):
    button_1 = KeyboardButton('/group')
    button_2 = KeyboardButton('/last')
    keyboard = [button_1]
    if button:
        keyboard.append(button_2)
    return ReplyKeyboardMarkup([keyboard])


def start(update, context):
    greetin = "I`m bot and this is testing"
    keyboard_markup = keyboard(button=False)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=greetin,
        reply_markup=keyboard_markup)


def insert_info(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Введите номер группы в формате 'XYZ-123456'",
        reply_markup=ReplyKeyboardRemove())
    return GROUP_NUMBER


def group(update, context):
    group_number = update.message.text
    # logger.info(update.message.reply_text(group_number))
    schedule_get = schedule(group_number)
    if schedule_get is not None:
        pass
    else:
        update.message.reply_text("Not such group number can be found")
        return GROUP_NUMBER
    return ConversationHandler.END


def cancel(update, context):
    start(update, context)
    return ConversationHandler.END


def main():
    # start bot
    updater = Updater(
        token='986948899:AAFBWnW1RNi4bTo84GRlz52NXccia_e-Q-Y',
        use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('group', insert_info)],
        states={
            GROUP_NUMBER: [MessageHandler(Filters.text, group)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        )

    # Adding handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


main()
