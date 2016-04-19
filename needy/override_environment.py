import os


class OverrideEnvironment:
    def __init__(self, vars_dict):
        self.__old_vals = dict()
        self.__new_vals = vars_dict
        self.__added_vals = []

        for k in vars_dict:
            if k in os.environ:
                self.__old_vals[k] = os.environ[k]
            else:
                self.__added_vals += [k]

    def __enter__(self):
        for k, v in self.__new_vals.items():
            os.environ[k] = v

    def __exit__(self, etype, value, traceback):
        for k, v in self.__old_vals.items():
            if k in os.environ:
                os.environ[k] = v
        for k in self.__added_vals:
            del os.environ[k]
