import os
import shutil
import time
import fcntl

from ..cache import Cache, KeyLocked, SourceNotFound, KeyNotFound
from ..filesystem import clean_file, lock_file


class Directory(Cache):
    def __init__(self, path):
        self.__path = path
        self.__locks = dict()

    @staticmethod
    def type():
        return 'directory'

    def to_dict(self):
        return {'path': self.__path}

    @staticmethod
    def from_dict(d):
        return Directory(path=d['path'])

    def description(self):
        return self.__path if self.__path else ''

    def store_file(self, source, key, timeout=0):
        destination_file = self.__archive_path(key)
        if not os.path.exists(source):
            raise SourceNotFound(source)
        try:
            clean_file(destination_file)
            shutil.copyfile(source, destination_file)
        except IOError:
            if key in self.__locks:
                raise
            else:
                raise KeyLocked(key)

    def load_file(self, key, destination, timeout=0):
        try:
            clean_file(destination)
            # Race condition between checking for existence and actually trying
            # the copy. Both will throw, but in the case where we lose the race,
            # the raised error will be a KeyLocked as opposed to a KeyNotFound.
            if not os.path.exists(self.__archive_path(key)):
                raise KeyNotFound(key)
            shutil.copyfile(self.__archive_path(key), destination)
        except IOError as e:
            raise KeyLocked(key, e)

    def exists(self, key):
        try:
            return os.path.exists(self.__archive_path(key))
        except IOError:
            if key in self.__locks:
                raise
            else:
                raise KeyLocked(key)

    def __archive_path(self, key=None):
        root = self.__path
        return os.path.join(root, key) if key else root

    def lock_key(self, key, timeout=None, create=False):
        if not create and not os.path.exists(self.__archive_path(key)):
            raise KeyNotFound(key)

        if create:
            try:
                os.makedirs(os.path.dirname(self.__archive_path(key)))
            except:
                pass

        fd = lock_file(self.__archive_path(key), timeout)
        if fd:
            self.__locks[key] = fd
        else:
            raise KeyLocked(key)

    def unlock_key(self, key):
        if key in self.__locks:
            os.close(self.__locks[key])
        else:
            raise KeyNotFound(key)

    def unset_key(self, key):
        if not os.path.exists(self.__archive_path(key)):
            return
        try:
            os.remove(self.__archive_path(key))
        except IOError:
            # TODO: how to determine errors for other reasons?
            if key in self.__locks:
                raise
            else:
                raise KeyLocked(key)
