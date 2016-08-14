import os
import shutil
import signal
import tempfile
import time
import json

from contextlib import contextmanager

O_BINARY = getattr(os, 'O_BINARY', 0)


class TempDir:
    def __enter__(self):
        self.__path = tempfile.mkdtemp()
        return self.__path

    def __exit__(self, etype, value, traceback):
        shutil.rmtree(self.__path)


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


def __win32_lock_fd(fd, timeout=None):
    '''returns True if the file descriptor is successfully locked'''
    import pywintypes
    import win32con
    import win32file
    import winerror

    try:
        handle = win32file._get_osfhandle(fd)

        if timeout is None:
            win32file.LockFileEx(handle, win32con.LOCKFILE_EXCLUSIVE_LOCK, 0, -0x10000, pywintypes.OVERLAPPED())
            return True

        if timeout > 0:
            start = time.time()
            while True:
                try:
                    win32file.LockFileEx(handle, win32con.LOCKFILE_EXCLUSIVE_LOCK | win32con.LOCKFILE_FAIL_IMMEDIATELY, 0, -0x10000, pywintypes.OVERLAPPED())
                    return True
                except pywintypes.error as e:
                    if e.winerror != winerror.ERROR_LOCK_VIOLATION:
                        break
                    time.sleep(0.05)
                    if time.time() > start + timeout:
                        break
        else:
            win32file.LockFileEx(handle, win32con.LOCKFILE_EXCLUSIVE_LOCK | win32con.LOCKFILE_FAIL_IMMEDIATELY, 0, -0x10000, pywintypes.OVERLAPPED())
            return True
    except pywintypes.error:
        pass
    return False


def __fcntl_lock_fd(fd, timeout=None):
    '''returns True if the file descriptor is successfully locked'''
    import fcntl
    try:
        if timeout is None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        elif timeout > 0:
            with SignalTimeout(timeout):
                fcntl.flock(fd, fcntl.LOCK_EX)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True


def lock_fd(fd, timeout=None):
    '''returns True if the file descriptor is successfully locked'''
    try:
        return __win32_lock_fd(fd, timeout)
    except ImportError:
        return __fcntl_lock_fd(fd, timeout)
    return False


def lock_file(file_path, timeout=None):
    '''returns file descriptor to newly locked file or None if file couldn't be locked'''
    fd = os.open(file_path, os.O_RDWR | os.O_CREAT | O_BINARY)
    try:
        if lock_fd(fd, timeout):
            return fd
    except:
        os.close(fd)
        raise
    os.close(fd)
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


def os_file(path, flags, mode):
    fd = os.open(path, flags)
    return os.fdopen(fd, mode)


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
