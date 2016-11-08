import hashlib
import os
import shutil
import time

from .file_cache import FileCache
from ..filesystem import clean_file


class DirectoryCache(FileCache):
    def __init__(self, path):
        self.__path = os.path.expanduser(path)
        self.prune()

    @staticmethod
    def type():
        return 'directory'

    @staticmethod
    def from_dict(d):
        return DirectoryCache(path=d['path'])

    def description(self):
        return self.__path if self.__path else ''

    def set(self, key, source):
        destination_file = self._object_path(key)
        clean_file(destination_file)
        shutil.copyfile(source, destination_file)
        return True

    def get(self, key, destination):
        try:
            shutil.copyfile(self._object_path(key), destination)
        except IOError:
            return False
        return True

    def prune(self, object_lifetime=60*60*24*7):
        if not os.path.exists(self.__path):
            return

        for name in os.listdir(self.__path):
            path = os.path.join(self.__path, name)
            s = os.stat(path)
            if name[0] != '.' and time.time() - s.st_atime >= object_lifetime:
                try:
                    os.remove(path)
                except IOError:
                    pass

    def _object_path(self, key):
        return os.path.join(self.__path, hashlib.sha256(key.encode()).hexdigest())
