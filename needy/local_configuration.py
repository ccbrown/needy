from __future__ import print_function

import json
import os
import sys

from .filesystem import lock_fd, os_file


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

        self.__file = os_file(self.__path, os.O_RDWR | os.O_CREAT, 'r+')

        if not lock_fd(self.__file.fileno(), timeout=0):
            if not self.__blocking:
                self.__file.close()
                self.__file = None
                return None
            print('Waiting for other needy instances to terminate...', file=sys.stderr)
            lock_fd(self.__file.fileno())

        contents = self.__file.read()
        if contents:
            self.__configuration = json.loads(contents)

        return self

    def __exit__(self, etype, value, traceback):
        if self.__file:
            self.__file.seek(0)
            self.__file.write(json.dumps(self.__configuration))
            self.__file.truncate()
            self.__file.close()

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
