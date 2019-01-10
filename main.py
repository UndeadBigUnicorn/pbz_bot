import telebot
import constants
from telebot import types
from flask import Flask, request
import sqlalchemy as db
import os

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'photodb.sqlite?check_same_thread=False')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
engine = db.create_engine(SQLALCHEMY_DATABASE_URI)  # check_same_thread=False)  # Create test.sqlite automatically
connection = engine.connect()
metadata = db.MetaData()
# photos2 = db.Table('photos', metadata, autoload=True, autoload_with=engine)
# photos2.drop(engine)
photos = db.Table('photos', metadata,
                  db.Column('id', db.Integer(), primary_key=True),  # nullable=False, autoincrement=True),
                  db.Column('file_id', db.String(255), nullable=False)
                  )

metadata.create_all(engine)  # Creates the table

TOKEN = constants.token
adminId = constants.adminId
channelId = constants.channelId

# secret = "285ufh4uqgf94"
url = "https://kravchel17.pythonanywhere.com/"  # + secret

bot = telebot.TeleBot(TOKEN, threaded=False)
bot.remove_webhook()
bot.set_webhook(url=url)

app = Flask(__name__)

user_keyboard = types.InlineKeyboardMarkup(row_width=1)
url_button = types.InlineKeyboardButton(text="Перейти в лучший канал с мемами", url="https://t.me/filtern_t")
user_keyboard.add(url_button)

keyboard = types.InlineKeyboardMarkup(row_width=2)
confirm_button = types.InlineKeyboardButton(text="Confrim", callback_data="confirm")
abort_button = types.InlineKeyboardButton(text="Abort", callback_data="abort")
keyboard.add(confirm_button, abort_button)


@app.route('/', methods=['POST', 'GET'])  # + secret, methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200


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

    bot.send_message(message.from_user.id, 'Ваше сообщение отправлено админам', reply_markup=user_keyboard)

    bot.send_message(adminId,
                     message.text + ' Прислал ' + message.from_user.username if not None else message.from_user.first_name + ' через @filtern_t_bot',
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

    bot.send_message(message.from_user.id, 'Ваша картинка отправлена админам', reply_markup=user_keyboard)

    bot.send_photo(adminId, message.photo[0].file_id,
                   caption='Прислал {} через @filtern_t_bot'.format(
                       message.from_user.username if not None else message.from_user.first_name), reply_markup=keyboard)

    photo_messages[message.photo[0].file_id] = message.from_user.username if not None else message.from_user.first_name

    addMode.remove(message.from_user.id)


video_messages = {}


@bot.message_handler(content_types=['video'])
def handle_video(message):
    chatId = message.chat.id
    if (chatId not in addMode):
        return

    if (message.text is not None and message.text.lower() == "/cancel"):
        addMode.remove(message.from_user.id)
        return

    bot.send_message(message.from_user.id, 'Ваше видео отправлена админам', reply_markup=user_keyboard)

    bot.send_video(adminId, message.video.file_id,
                   caption='Прислал {} через @filtern_t_bot'.format(
                       message.from_user.username if not None else message.from_user.first_name), reply_markup=keyboard)

    video_messages[message.video.file_id] = message.from_user.username if not None else message.from_user.first_name

    addMode.remove(message.from_user.id)


sticker_messages = {}


@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    print(message)
    chatId = message.chat.id
    if (chatId not in addMode):
        return

    if (message.text is not None and message.text.lower() == "/cancel"):
        addMode.remove(message.from_user.id)
        return

    bot.send_message(message.from_user.id, 'Ваш стикер отправлен админам', reply_markup=user_keyboard)

    bot.send_sticker(adminId, message.sticker.file_id, reply_markup=keyboard)

    sticker_messages[message.sticker.file_id] = message.from_user.username if not None else message.from_user.first_name

    addMode.remove(message.from_user.id)


gif_messages = {}


@bot.message_handler(content_types=['document'])
def handle_gif(message):
    chatId = message.chat.id
    if (chatId not in addMode):
        return

    if (message.text is not None and message.text.lower() == "/cancel"):
        addMode.remove(message.from_user.id)
        return

    bot.send_message(message.from_user.id, 'Ваша гифка отправлена админам', reply_markup=user_keyboard)

    bot.send_document(adminId, message.document.file_id, caption='Прислал {} через @filtern_t_bot'.format(
        message.from_user.username if not None else message.from_user.first_name), reply_markup=keyboard)

    gif_messages[message.document.file_id] = message.from_user.username if not None else message.from_user.first_name

    addMode.remove(message.from_user.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "confirm":
            if call.message.photo:
                bot.send_photo(channelId, call.message.photo[0].file_id,
                               caption='Прислал {} через @filtern_t_bot'.format(
                                   photo_messages[call.message.photo[0].file_id]))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отправлено @{}".format(call.from_user.username))
                query = db.insert(photos).values(file_id=call.message.photo[0].file_id)
                ResultProxy = connection.execute(query)
                del photo_messages[call.message.photo[0].file_id]
            elif call.message.video:
                bot.send_video(channelId, call.message.video.file_id,
                               caption='Прислал {} через @filtern_t_bot'.format(
                                   video_messages[call.message.video.file_id]))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отправлено @{}".format(call.from_user.username))
                del video_messages[call.message.video.file_id]
            elif call.message.sticker:
                bot.send_sticker(channelId, call.message.sticker.file_id)
                bot.send_message(channelId,
                                 'Прислал {} через @filtern_t_bot'.format(
                                     sticker_messages[call.message.sticker.file_id]))
                del sticker_messages[call.message.sticker.file_id]
            elif call.message.document:
                bot.send_document(channelId, call.message.document.file_id,
                                  caption='Прислал {} через @filtern_t_bot'.format(
                                      gif_messages[call.message.document.file_id]))
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отправлено @{}".format(call.from_user.username))
                del gif_messages[call.message.document.file_id]
            else:
                bot.send_message(channelId, call.message.text)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Отправлено")
            # Уведомление в верхней части экрана
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Сообщение отправлено на канал")

        if call.data == "abort":
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отменено @{}".format(call.from_user.username))
                del photo_messages[call.message.photo[0].file_id]
            elif call.message.video:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отменено @{}".format(call.from_user.username))
                del video_messages[call.message.video.file_id]
            elif call.message.sticker:
                del sticker_messages[call.message.sticker.file_id]
            elif call.message.document:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                         caption="Отменено @{}".format(call.from_user.username))
                del gif_messages[call.message.document.file_id]
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Отменено @{}".format(call.from_user.username))
            bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="Сообщение отменено")


@bot.inline_handler(lambda query: len(query.query) >= 0)
def empty_query(query):
    try:
        array = []
        query_sql = db.select([photos])
        ResultProxy = connection.execute(query_sql)
        ResultSet = ResultProxy.fetchall()  # Result of query
        for i in ResultSet:
            array.append(types.InlineQueryResultCachedPhoto(id=i.id, photo_file_id=i.file_id, parse_mode='Markdown'))
        bot.answer_inline_query(query.id, array, cache_time=2)
    except Exception as e:
        print(e)
