import os

from text_transliter import *


class FileExtractor(object):
    """file from user which has been sent in bot"""

    def __init__(self):
        pass

    @staticmethod
    def _get_file_user_sent(telebot, message):
        # get file and filename which have been sent by user in bot
        file_info = telebot.get_file(message.document.file_id)
        downloaded_file = telebot.download_file(file_info.file_path)
        filename = TextTransliter(message.document.file_name).get_translitet()
        return downloaded_file, filename

    def local_save_file(self, telebot, message, download_path):
        # save file from user to local folder
        downloaded_file, filename = self._get_file_user_sent(telebot, message)
        # todo make it throw regex, ept
        if (filename.find('.epub') != -1):
            # file_from_user = save_file(downloaded_file, path_for_save, filename)
            path_for_save = os.path.join(download_path, filename.isalnum())
            with open(path_for_save, 'wb') as new_file:
                new_file.write(downloaded_file)
            return path_for_save
        else:
            return -1  # type error
