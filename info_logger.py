import logging


class BotLogger(object):
    """ Logs with now time and join all input parameters"""

    def __init__(self, level2=logging.INFO):

        logging.basicConfig(filename="log.txt",
                            format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
                            level=logging.INFO)

    @staticmethod
    def _join_args(*args):
        tmp_list = []
        tmp_list.extend(args)
        return ' '.join(map(str, tmp_list))

    def log_message(self, message):
        user_id, chat_id = message.from_user.id, message.chat.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        username = message.from_user.username
        self.info('Received message.',
                  'first_name, last_name, user_name, user_id, chat_id',
                  first_name, last_name, username, user_id, chat_id,
                  message.text)

    def log_sent(self, user_id='', chat_id='', msg=''):
        self.info('Sent to user_id, chat_id: ', user_id, chat_id,
                  'Message:', msg)

    def info(self, *args):
        try:
            log_issue = self._join_args(args)
            logging.info(log_issue)
        except Exception as e:
            pass

    def error(self, *args):
        try:
            log_issue = self._join_args(args)
            logging.error(log_issue)
        except Exception as e:
            pass
