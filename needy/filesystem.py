import os
import fcntl
import signal
import tempfile
import shutil
import json

from contextlib import contextmanager


class TempDir:
    def __enter__(self):
        self.__path = tempfile.mkdtemp()
        return self.__path

    def __exit__(self, etype, value, traceback):
        shutil.rmtree(self.__path)

    def path(self):
        return self.__path


class SignalTimeout:
    def __init__(self, seconds):
        self.__seconds = seconds

    @staticmethod
    def timeout_handler(signum, frame):
        pass

    def __enter__(self):
        self.__previous_handler = signal.signal(signal.SIGALRM, SignalTimeout.timeout_handler)
        signal.alarm(self.__seconds)

    def __exit__(self, etype, value, traceback):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.__previous_handler)


def lock_file(file_path, timeout=None):
    '''returns file descriptor to newly locked file or None if file couldn't be locked'''
    fd = os.open(file_path, os.O_RDWR | os.O_CREAT)
    try:
        if timeout is None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        elif timeout > 0:
            with SignalTimeout(timeout):
                fcntl.flock(fd, fcntl.LOCK_EX)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        pass
    return None


def clean_file(file_path):
    parent_dir = os.path.dirname(file_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    elif os.path.exists(file_path):
        os.remove(file_path)


def clean_directory(directory_path):
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path)


@contextmanager
def dict_file(path):
    d = dict()
    if os.path.exists(path):
        with open(path, 'r') as f:
            contents = f.read()
            if contents:
                d = json.loads(contents)
    yield d
    with open(path, 'w') as f:
        json.dump(d, f)
