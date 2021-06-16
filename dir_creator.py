import errno
import os


class DirCreator(object):
    """create new working directory"""

    new_path = ''

    def __init__(self, new_path=''):
        self.new_path = new_path
        self._create_directory_if_no_exist()

    def _create_directory_if_no_exist(self):
        try:
            os.makedirs(self.new_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        pass
