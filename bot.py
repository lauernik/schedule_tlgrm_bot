# Бот предоставляет расписание студентам УРФУ
# Bot present schedule for UrFU students
# @schedule_urfu_tlgrm
# Version 0.2.1

# Import
from telegram import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ChatAction)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
import logging
from parser import schedule
from functools import wraps
import os
import psycopg2

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
    db_user_add(update, context)


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
        db_number_add(update, context, group_number)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_for_search(),
            reply_markup=keyboard())
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
            else:
                message += 'Свободный день'
            update.message.reply_text(message)
            i += 1
        else:
            break


def cancel(update, context):
    start(update, context)
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def conn_db():
    # Подключаем базу данных
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn


# Добавляем юзернейма в базу данных
def db_user_add(update, context):
    user_id = update.message.chat.id
    con = conn_db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
    # logger.info(cur)
    # Проверка на присутствие айди в базе данных
    if cur.fetchone():
        pass
    # Если нет, то добавляем
    else:
        cur.execute("INSERT INTO users VALUES (%s);",(user_id,))
        con.commit()
    cur.close()
    con.close()


#
def db_number_add(update, context, last_number):
    user_id = update.message.chat.id
    con = conn_db()
    cur = con.cursor()
    cur.execute("UPDATE users SET last_number = (%s) WHERE user_id = (%s);",
                (last_number, user_id))
    con.commit()
    cur.close()
    con.close()


def db_number_get(update, context):
    user_id = update.message.chat.id
    con = conn_db()
    cur = con.cursor()
    cur.execute("SELECT last_number FROM users where user_id = (%s);",
                (user_id,))
    group_number = cur.fetchone()
    cur.close()
    con.close()
    return group_number


def last(update, context):
    group_number = db_number_get(update, context)
    schedule_get = schedule(group_number)
    schedule_messages(update, context, schedule_get, group_number)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text_for_search(),
        reply_markup=keyboard())


def text_for_search():
    return 'Для нового поиска нажми /group или /last'


def main():
    # start bot
    TOKEN = '986948899:AAFBWnW1RNi4bTo84GRlz52NXccia_e-Q-Y'
    NAME = 'evening-plateau-67761'

    # Порт даёт Heroku
    PORT = os.environ.get('PORT')

    updater = Updater(
        token=TOKEN,
        use_context=True)
    dispatcher = updater.dispatcher

    # Adding handlers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('group', insert_info)],
        states={
            GROUP_NUMBER: [MessageHandler(Filters.text, group)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        )

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)
    dispatcher.add_handler(CommandHandler('last', last))

    # updater.start_polling()  # Старт опроса

    # Конфигурация вебхука
    updater.start_webhook(listen='0.0.0.0',
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))

    # Используется при завершении
    updater.idle()


if __name__ == "__main__":
    main()
