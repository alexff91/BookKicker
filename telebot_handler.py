import sys

import telebot
from apscheduler.schedulers.background import BackgroundScheduler
import time
import flask

import config
import tokens
from book_adder import BookAdder
from book_reader import BookReader
from books_library import BooksLibrary
from file_extractor import FileExtractor
from info_logger import BotLogger
from gtts import gTTS

secret = "GUID"

token = tokens.test_token
if '--prod' in sys.argv:
    token = tokens.production_token

webhook_host = tokens.ruvds_server_ip  # server ruvds
webhook_url_base = "https://%s:%s" % (webhook_host, config.webhook_port)
webhook_url_path = "/%s/" % token

# tb = telebot.TeleBot(token, threaded=False)
tb = telebot.TeleBot(token)
tb.remove_webhook()
time.sleep(1)
tb.set_webhook(url=webhook_url_base + webhook_url_path,
               certificate=open(config.webhook_ssl_cert, 'r'))

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(webhook_url_path, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        tb.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


# init classes
book_reader = BookReader()
book_adder = BookAdder()
books_library = BooksLibrary()
commands = ['/help', '/more', '/skip', '/auto_status', '/now_reading', '/change_lang', '/audio']
lang_list = ['en', 'ru']
audio_list = ['on', 'off']
logger = BotLogger()
logger.info('Telebot has been started')

poem_mode_user_id_list = set()  # set of user_id which choose poem_mode before sending a book file


def markup(clist):
    if len(clist) == 0:
        # remove_markup = telebot.types.ReplyKeyboardHide(True) # for old versions of teelbot
        return telebot.types.ReplyKeyboardRemove(True)
    user_markup = telebot.types.ReplyKeyboardMarkup(True,
                                                    one_time_keyboard=True)
    for item in clist:
        user_markup.row(item)
    return user_markup


user_markup_normal = markup(commands)


@tb.message_handler(commands=['start'])
def start_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        lang = books_library.get_lang(user_id)
        msg = config.message_success_start[lang]
        tb.send_message(chat_id, msg,
                        reply_markup=markup(['/help']))
        logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['auto_status'])
def view_autostatus(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        # logger.log_message(message)
        # 1 means auto is ON
        is_auto_ON = (books_library.get_auto_status(user_id) == 1)
        markup_list = ['/more', '/help']
        if is_auto_ON:
            markup_list.append('/stop_auto')
            msg = config.message_everyday_ON[lang]
        else:
            markup_list.append('/start_auto')
            msg = config.message_everyday_OFF[lang]
        tb.send_message(chat_id, msg, reply_markup=markup(markup_list))
        # logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        # logger.error(e)


@tb.message_handler(commands=['stop_auto', 'start_auto'])
def change_autostatus(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        # 1 means auto is ON
        logger.log_message(message)
        if switch_needed(message):
            books_library.switch_auto_staus(user_id)
        view_autostatus(message)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


def switch_needed(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    is_auto_ON = (books_library.get_auto_status(user_id) == 1)
    command = message.text.replace('/', '')
    # update only if ON+stop OR OFF+start:
    legitimate_stop = is_auto_ON and command == 'stop_auto'
    legitimate_start = not is_auto_ON and command == 'start_auto'
    need = legitimate_stop or legitimate_start
    return need


# @tb.message_handler(commands=['my_books'])
# def show_user_books(message):
#     try:
#         user_id, chat_id = message.from_user.id, message.chat.id
#         logger.log_message(message)
#         tb.send_chat_action(chat_id, 'typing')
#         books_list = books_library.get_user_books(user_id)
#         msg, user_markup = books_list_message(books_list, user_id)
#         tb.send_message(chat_id, msg, reply_markup=user_markup)
#         logger.log_sent(user_id, chat_id, msg)
#         tb.register_next_step_handler(message, process_change_book)
#     except Exception as e:
#         tb.reply_to(message, e)
#         logger.error(e)


def books_list_message(books_list, user_id):
    # prepare message and keyboard by list of user's books
    lang = books_library.get_lang(user_id)
    if len(books_list) == 0:
        msg = config.message_empty_booklist[lang]
        return msg, markup(['/help'])
    msg = str(config.message_booklist[lang])
    markup_list = []
    for book in books_list:
        msg += '\t' + str(book).replace(str(user_id) + '_', '') + '\n'
        markup_list.append('/' + str(book).replace(str(user_id) + '_', ''))
    msg += str(config.message_choose_book[lang])
    return msg, markup(markup_list)


def process_change_book(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        lang = books_library.get_lang(user_id)
        new_book = message.text.replace('/', '')
        new_book = str(user_id) + '_' + new_book
        tb.send_chat_action(chat_id, 'typing')
        books_list = books_library.get_user_books(user_id)
        if new_book in books_list:
            books_library.update_current_book(user_id, chat_id, new_book)
            book_name = books_library.get_current_book(user_id,
                                                       format_name=True)
            msg = config.message_now_reading[lang].format(book_name)
            tb.send_message(chat_id, msg,
                            reply_markup=markup(['/more', '/help']))
            logger.log_sent(user_id, chat_id, msg)
        else:
            msg = config.error_book_recognition[lang]
            tb.send_message(chat_id, msg)
            logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['more'])
def listener(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        # logger.log_message(message)
        send_portion(user_id, chat_id, 0)
    except Exception as e:
        tb.reply_to(message, e)
        # logger.error(e)


@tb.message_handler(commands=['skip'])
def listener(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        # logger.log_message(message)
        send_portion(user_id, chat_id, 100)
    except Exception as e:
        tb.reply_to(message, e)
        # logger.error(e)


@tb.message_handler(commands=['help'])
def help_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        tb.send_chat_action(chat_id, 'typing')
        lang = books_library.get_lang(user_id)
        msg = config.message_help[lang]
        tb.send_message(chat_id, msg, reply_markup=user_markup_normal)
        logger.log_sent(user_id, chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['sayhi'])
def sayhi_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        tb.send_message(chat_id, 'Hi sir!')
        logger.log_sent(user_id, chat_id, 'Hi sir!')
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['now_reading'])
def now_reading_handler(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        tb.send_chat_action(chat_id, 'typing')
        logger.log_message(message)
        book_name = now_reading_answer(user_id)
        tb.send_message(chat_id, book_name,
                        reply_markup=user_markup_normal)
        logger.log_sent(user_id, chat_id, book_name)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


def now_reading_answer(user_id):
    # prepare answer for now reading.
    # If no info, returns error message from config
    book_name = books_library.get_current_book(user_id, format_name=True)
    if book_name == -1:
        lang = books_library.get_lang(user_id)
        return config.error_current_book[lang]
    return book_name


def _get_user_send_mode(user_id):
    user_send_mode = 'by_sense'
    if user_id in poem_mode_user_id_list:
        # if user set poem_mode, remember it and delete from query
        user_send_mode = 'by_newline'
        poem_mode_user_id_list.remove(user_id)
    return user_send_mode


# maybe once you could make it better
# @bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
@tb.message_handler(content_types=['document'])
def handle_document(message):
    try:
        user_id, chat_id = message.from_user.id, message.chat.id
        logger.log_message(message)
        lang = books_library.get_lang(user_id)
        path_for_save = config.path_for_save
        file_extractor = FileExtractor()
        tb.send_chat_action(chat_id, 'typing')
        local_file_path = file_extractor.local_save_file(tb, message,
                                                         path_for_save)
        if local_file_path != -1:
            book_adder.add_new_book(user_id, chat_id, local_file_path,
                                    sending_mode="by_sense")
            msg = config.message_file_added[lang]
            tb.send_message(chat_id, msg, reply_markup=markup([]))
            logger.log_sent(user_id, chat_id, msg)
        else:
            msg = config.error_file_type[lang]
            tb.send_message(chat_id, msg)
    except Exception as e:
        tb.reply_to(message, e)
        logger.error(e)


@tb.message_handler(commands=['change_lang'])
def change_lang_handler(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    logger.log_message(message)
    msg = 'Choose language on keyboard\n'
    tb.send_message(chat_id, msg, reply_markup=markup(lang_list))
    logger.log_sent(user_id, chat_id, msg)
    tb.register_next_step_handler(message, change_lang)

@tb.message_handler(commands=['audio'])
def change_lang_handler(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    logger.log_message(message)
    msg = 'Включить или выключить режим аудиокниги\n'
    tb.send_message(chat_id, msg, reply_markup=markup(audio_list))
    logger.log_sent(user_id, chat_id, msg)
    tb.register_next_step_handler(message, change_audio)

def change_lang(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    cur_lang = books_library.get_lang(user_id)
    new_lang = message.text
    if new_lang in lang_list:
        books_library.update_lang(user_id, new_lang)
        msg = config.message_lang_changed[new_lang]
    else:
        msg = config.error_lang_recognition[cur_lang]
    tb.send_message(chat_id, msg)
    logger.log_sent(user_id, chat_id, msg)

def change_audio(message):
    user_id, chat_id = message.from_user.id, message.chat.id
    cur_lang = books_library.get_lang(user_id)
    new_audio = message.text
    if new_audio in audio_list:
        books_library.update_audio(user_id, new_audio)
        msg = config.message_audio_changed[cur_lang]
    else:
        msg = config.error_audio_recognition[cur_lang]
    tb.send_message(chat_id, msg)
    logger.log_sent(user_id, chat_id, msg)

@tb.message_handler(func=lambda message: True, content_types=['text'])
def command_default(message):
    # this is the standard reply to a normal message
    user_id, chat_id = message.from_user.id, message.chat.id
    logger.log_message(message)
    lang = books_library.get_lang(user_id)
    msg = config.message_dont_understand[lang].format(message.text)
    tb.send_message(chat_id, msg)
    logger.log_sent(user_id, chat_id, msg)


def book_finished(portion):
    if config.end_book_string in portion:
        return True
    if portion == '/more':
        return True
    return False


def turn_off_autostatus(user_id, chat_id):
    # turn off autostatus if book was finished
    if books_library.get_auto_status(user_id):
        books_library.switch_auto_staus(user_id)
        lang = books_library.get_lang(user_id)
        auto_off_msg = config.message_everyday_OFF[lang]
        user_markup = markup(['/start_auto'])
        tb.send_message(chat_id, auto_off_msg, reply_markup=user_markup)


def send_portion(user_id, chat_id, offset):
    logger.info('Sending action TYPING: ', user_id, chat_id)
    tb.send_chat_action(chat_id, 'typing')
    msg = book_reader.get_next_portion(user_id, offset)
    lang = books_library.get_lang(user_id)
    res = 0
    if msg is None:
        msg = config.error_user_finding[lang]
        res = -1
    elif book_finished(msg):
        msg += config.message_book_finished[
                   lang] + '/n /start_auto'
        turn_off_autostatus(user_id, chat_id)
    else:
        msg += '\n/more'
    m_size = config.max_msg_size  # max message size
    audio = books_library.get_audio(user_id)
    while len(msg) > 0:
        logger.info('Send to u_id, c_id: ', user_id, chat_id, 'Message:', msg)
        tb.send_message(chat_id, msg[:m_size], reply_markup=markup([]), parse_mode='Markdown')
        if audio == 'on':
            tts = gTTS(msg[:m_size], lang='ru')
            tts.save(str(chat_id) + '.ogg')
            audio = open(str(chat_id) + '.ogg', 'rb')
            tb.send_voice(chat_id, audio, disable_notification=True)
        msg = msg[m_size:]
    logger.info('OK')
    return res


def auto_send_portions():
    send_list = books_library.get_users_for_autosend()
    for item in send_list:
        try:
            user_id, chat_id = item[0], item[1]
            send_portion(user_id, chat_id, 0)
        except Exception as e:
            pass
            logger.error(e)
    return 0


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_send_portions, 'cron', hour='5,6,7,8,9,10,11,12,13,14,15,16,17', misfire_grace_time=3600)
    scheduler.start()
    if '--prod' in sys.argv:
        while True:
            try:
                # Start flask server
                app.run(host=config.webhook_listen,
                        port=config.webhook_port,
                        ssl_context=(
                            config.webhook_ssl_cert,
                            config.webhook_ssl_priv),
                        debug=False)
            except Exception as e:
                logger.error(e)
                print(e)
                time.sleep(5)
    else:
        tb.remove_webhook()
        while True:
            try:
                tb.polling(none_stop=True)
            except Exception as e:
                logger.error(e)
                print(e)
                time.sleep(5)
