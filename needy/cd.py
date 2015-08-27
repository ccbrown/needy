import os

_current_directory = None

def current_directory():
    """ returns the current directory as given to cd (which means unresolved symlinks) """
    global _current_directory
    return _current_directory or os.getcwd()

class cd:
    def __init__(self, new_path):
        self.__new_path = os.path.expanduser(new_path)

    def __enter__(self):
        global _current_directory
        self.__saved_path = os.getcwd()
        os.chdir(self.__new_path)
        _current_directory = self.__new_path

    def __exit__(self, etype, value, traceback):
        global _current_directory
        os.chdir(self.__saved_path)
        _current_directory = None
