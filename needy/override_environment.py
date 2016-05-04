import os


class OverrideEnvironment:
    def __init__(self, vars_dict):
        self.__old_vals = dict()
        self.__new_vals = vars_dict
        self.__added_vals = []

        for k, v in vars_dict.items():
            if k in os.environ:
                self.__old_vals[k] = os.environ[k]
            elif v is not None:
                self.__added_vals += [k]

    def __enter__(self):
        for k, v in self.__new_vals.items():
            if v is None:
                if k in os.environ:
                    del os.environ[k]
            else:
                os.environ[k] = v

    def __exit__(self, etype, value, traceback):
        for k, v in self.__old_vals.items():
            os.environ[k] = v
        for k in self.__added_vals:
            del os.environ[k]
