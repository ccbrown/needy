import os
import fcntl
import signal


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
