import telebot
import constants
import cherrypy
import os
from telebot import types

TOKEN = os.environ['TOKEN']
adminId = constants.adminId
channelId = constants.channelId
bot = telebot.TeleBot(TOKEN)

WEBHOOK_HOST = 'https://pbzbot.herokuapp.com'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше


WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


bot.remove_webhook()

# Ставим заново вебхук
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

# Указываем настройки сервера CherryPy
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin'
})


"""
WEBHOOK_HOST = 'https://pbzbot.herokuapp.com'  # name your app
WEBHOOK_PATH = '/webhook/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.environ.get('PORT')
"""

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.from_user.id, """Этот бот позволяет отправлять контент админам канала Приматы без фильтра.\n
Для отправки сообщения используйте команду:\n
`/send`\n""")


@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.from_user.id, "По всем вопросам писать @UndeadBigUnicorn")


addMode = []
photo_messages = {}


@bot.message_handler(commands=['send'])
def handle_send(message):
    text = 'Теперь пришлите ваше сообщение. Или /cancel для отмены операции.'
    addMode.append(message.from_user.id)
    bot.send_message(message.from_user.id, text);


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chatId = message.chat.id;
    if (chatId not in addMode):
        return

    if (message.text is not None and message.text.lower() == "/cancel"):
        addMode.remove(message.from_user.id)
        return

    user_keyboard = types.InlineKeyboardMarkup(row_width=1)
    url_button = types.InlineKeyboardButton(text="Перейти в лучший чат с мемами", url="https://t.me/filtern_t")
    user_keyboard.add(url_button)
    bot.send_message(message.from_user.id, 'Ваше сообщение отправлено админам', reply_markup=user_keyboard)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton(text="Confrim", callback_data="confirm")
    abort_button = types.InlineKeyboardButton(text="Abort", callback_data="abort")
    keyboard.add(confirm_button, abort_button)

    bot.send_message(adminId, message.text + ' Прислал ' + message.from_user.username + ' через бота',
                     reply_markup=keyboard)

    addMode.remove(message.from_user.id)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chatId = message.chat.id
    if (chatId not in addMode):
        return

    if (message.text is not None and message.text.lower() == "/cancel"):
        addMode.remove(message.from_user.id)
        return

    user_keyboard = types.InlineKeyboardMarkup(row_width=1)
    url_button = types.InlineKeyboardButton(text="Перейти в лучший чат с мемами", url="https://t.me/filtern_t")
    user_keyboard.add(url_button)
    bot.send_message(message.from_user.id, 'Ваша картинка отправлено админам', reply_markup=user_keyboard)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    confirm_button = types.InlineKeyboardButton(text="Confrim", callback_data="confirm")
    abort_button = types.InlineKeyboardButton(text="Abort", callback_data="abort")
    keyboard.add(confirm_button, abort_button)

    bot.send_photo(adminId, message.photo[0].file_id,
                   caption='Прислал {} через бота'.format(message.from_user.username), reply_markup=keyboard)

    photo_messages[message.photo[0].file_id] = message.from_user.username

    addMode.remove(message.from_user.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):  # в call можно еще смотреть, кто нажал
    if call.message:
        if call.data == "confirm":
            if call.message.photo:
                bot.send_photo(channelId, call.message.photo[0].file_id,
                               caption='Прислал {} через бота'.format(photo_messages[call.message.photo[0].file_id]))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отправлено")
                del photo_messages[call.message.photo[0].file_id]
            else:
                bot.send_message(channelId, call.message.text)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Отправлено")
            # Уведомление в верхней части экрана
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Сообщение отправлено на канал")
        if call.data == "abort":
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отменено")
                del photo_messages[call.message.photo[0].file_id]
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Отменено")
            bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="Сообщение отменено")


#bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':
    # Собственно, запуск!
    cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
