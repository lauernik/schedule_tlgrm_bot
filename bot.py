# Бот предоставляет расписание студентам УРФУ
# Bot present schedule for UrFU students
# @schedule_urfu_tlgrm
# Version 0.3

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
from boto.s3.connection import S3Connection

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

GROUP_NUMBER = 0

# Define command for Handlers and other

# Декоратор, для эффекта "печает..."
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
    button_1 = KeyboardButton('Новый поиск')
    button_2 = KeyboardButton('Повтор')
    if button:
        return ReplyKeyboardMarkup([[button_1],
                                    [button_2]],
                                    resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([[button_1]], resize_keyboard=True)


def start(update, context):
    greetin = "Привет. Я помогу узнать расписание на ближайшие 3 дня.\nНажми /group и введи номер группы"
    keyboard_markup = keyboard(button=False)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=greetin,
        reply_markup=keyboard_markup)
    db_user_add(update, context)

# Выводит сообщение юзеру и убирает кастомную клавиатуру
def insert_info(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Введи номер группы в формате 'XYZ-123456'",
        reply_markup=ReplyKeyboardRemove())
    return GROUP_NUMBER


# Функция показывает расписание,
# работает, когда вводится новая группа
@send_action(ChatAction.TYPING)
def group(update, context):
    group_number = update.message.text
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


# Вывод расписания сообщениями
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


# Переход в начало, необходима для ConversationHandler`а
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
    # Проверка на присутствие айди в базе данных
    if cur.fetchone():
        pass
    # Если нет, то добавляем
    else:
        cur.execute("INSERT INTO users VALUES (%s);",(user_id,))
        con.commit()
    cur.close()
    con.close()


# Добавляем номер группы к юзеру
def db_number_add(update, context, last_number):
    user_id = update.message.chat.id
    con = conn_db()
    cur = con.cursor()
    cur.execute("UPDATE users SET last_number = (%s) WHERE user_id = (%s);",
                (last_number, user_id))
    con.commit()
    cur.close()
    con.close()


# Получаем номер группы
def db_number_get(update, context):
    user_id = update.message.chat.id
    con = conn_db()
    cur = con.cursor()
    cur.execute("SELECT last_number FROM users where user_id = (%s);",
                (user_id,))
    group_number_tuple = cur.fetchone()
    group_number = group_number_tuple[0]
    cur.close()
    con.close()
    return group_number


# Расписание для предыдущей группы, берется из базы данных
@send_action(ChatAction.TYPING)
def last(update, context):
    group_number = db_number_get(update, context)
    schedule_get = schedule(group_number)
    schedule_messages(update, context, schedule_get, group_number)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text_for_search(),
        reply_markup=keyboard())


def text_for_search():
    return 'Нажми "Повтор" либо "Новый поиск" для ввода другой группы'


def main():
    s3 = S3Connection(os.environ['S3_KEY'], os.environ['S3_SECRET'])
    # start bot
    TOKEN = os.environ.get('TLGRM_API_KEY_SCHDL')
    NAME = os.environ.get('APP_SCHDL')

    # Порт даёт Heroku
    PORT = os.environ.get('PORT')

    updater = Updater(
        token=TOKEN,
        use_context=True)
    dispatcher = updater.dispatcher

    # Adding handlers
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(r'Новый поиск'), insert_info)],
        states={
            GROUP_NUMBER: [MessageHandler(Filters.text, group)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
        )

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)
    dispatcher.add_handler(MessageHandler(Filters.regex(r'Повтор'), last))

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
