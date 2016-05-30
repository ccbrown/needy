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

        return self

    def __exit__(self, etype, value, traceback):
        with open(self.__path, 'wt') as f:
            json.dump(self.__configuration, f)
        os.close(self.__fd)
