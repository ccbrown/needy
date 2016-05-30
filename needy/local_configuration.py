import fcntl
import json
import os
import sys


class LocalConfiguration:
    """ This is a context manager that obtains exclusive read and write access to the given file."""

    def __init__(self, path, blocking=True):
        self.__path = path
        self.__configuration = {}
        self.__blocking = blocking

    def __enter__(self):
        directory = os.path.dirname(self.__path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except os.error as e:
                if not os.path.exists(directory):
                    raise e

        self.__fd = os.open(self.__path, os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(self.__fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            if not self.__blocking:
                return None
            print('Waiting for other needy instances to terminate...')
            fcntl.flock(self.__fd, fcntl.LOCK_EX)

        with open(self.__path, 'rt') as f:
            contents = f.read()
            if contents:
                self.__configuration = json.loads(contents)

        return self

    def __exit__(self, etype, value, traceback):
        with open(self.__path, 'wt') as f:
            json.dump(self.__configuration, f)
        os.close(self.__fd)

    def development_mode(self, library_name):
        return self.__library_configuration(library_name, 'development_mode', False)

    def set_development_mode(self, library_name, enable=True):
        self.__set_library_configuration(library_name, 'development_mode', enable)

    def __library_configuration(self, library_name, key, default=None):
        if 'libraries' not in self.__configuration or library_name not in self.__configuration['libraries']:
            return default
        return self.__configuration['libraries'][library_name][key]

    def __set_library_configuration(self, library_name, key, value):
        if 'libraries' not in self.__configuration:
            self.__configuration['libraries'] = {}
        if library_name not in self.__configuration['libraries']:
            self.__configuration['libraries'][library_name] = {}
        self.__configuration['libraries'][library_name][key] = value
