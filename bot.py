from telegram.ext import Updater, CommandHandler
import logging

updater = Updater(
    token='986948899:AAFBWnW1RNi4bTo84GRlz52NXccia_e-Q-Y',
    use_context=True)

dispatcher = updater.dispatcher

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def start(update, context):
    greetin = 'I`m bot and this is testing'
    context.bot.send_message(chat_id=update.effective_chat.id, text=greetin)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater.start_polling()
