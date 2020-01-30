# Бот предоставляет расписание студентам УРФУ
# Bot present schedule for UrFU students
# Version 0.1

# Import
from telegram import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ChatAction)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
import logging
from parser import schedule
from functools import wraps

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

GROUP_NUMBER = 0

# Define command for Handlers and other


def send_action(action):

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id,
                action=action
                )
            return func(update, context,  *args, **kwargs)
        return command_func
    return decorator


def keyboard(button=True):
    button_1 = KeyboardButton('/group')
    button_2 = KeyboardButton('/last')  # Предыдущая введеная группа (будущее)
    keyboard = [button_1]
    if button:
        keyboard.append(button_2)
    return ReplyKeyboardMarkup([keyboard])


def start(update, context):
    greetin = "Привет. Я помогу узнать расписание на ближайшие 3 дня.\nНажми /group и введи номер группы"
    keyboard_markup = keyboard(button=False)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=greetin,
        reply_markup=keyboard_markup)


def insert_info(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Введи номер группы в формате 'XYZ-123456'",
        reply_markup=ReplyKeyboardRemove())
    return GROUP_NUMBER


@send_action(ChatAction.TYPING)
def group(update, context):
    group_number = update.message.text
    # logger.info(update.message.reply_text(group_number))
    schedule_get = schedule(group_number)
    if schedule_get is not None:
        schedule_messages(update, context, schedule_get, group_number)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Для нового поиска нажми /group",
            reply_markup=keyboard(button=False))
    else:
        update.message.reply_text("Такая группа не найдена, попробуй ещё раз)")
        return GROUP_NUMBER
    return ConversationHandler.END


def schedule_messages(update, context, schedule, number):
    i = 0
    update.message.reply_text(
        'Расписание для группы {} на 3 дня'.format(number)
        )
    for key, values in schedule.items():
        if i < 3:
            message = ''
            message += key + '\n\n'
            if values:
                for value in values:
                    message += value + '\n'
                message += '\nwhat`s is goin` on?\n'
            else:
                message += 'Свободный день'
            i += 1
        else:
            break


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
