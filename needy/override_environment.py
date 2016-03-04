import os


class OverrideEnvironment:
    def __init__(self, vars_dict):
        self.__old_vals = dict()
        self.__new_vals = vars_dict

        for k in vars_dict:
            self.__old_vals[k] = os.environ[k]

    def __enter__(self):
        for k, v in self.__new_vals.iteritems():
            os.environ[k] = v

    def __exit__(self, etype, value, traceback):
        for k, v in self.__old_vals.iteritems():
            os.environ[k] = v
